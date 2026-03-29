"""
api/auth.py — 认证模块
注册、登录、忘记密码、邮箱验证
"""
import uuid as _uuid
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, create_refresh_token

from backend.extensions import db, limiter
from backend.models.user import User
from backend.models.verify_code import VerifyCode
from backend.middleware.auth_required import jwt_required_custom
from backend.utils.response import success, error
from backend.utils.validators import validate_email, validate_password
from backend.utils.analytics_tracker import track_register, track_login
from services.email_sender import send_verify_code as send_email_code
import config


def create_blueprint():
    bp = Blueprint("auth", __name__, url_prefix="/auth")

    @bp.route("/register", methods=["POST"])
    @limiter.limit("10 per hour")
    def register():
        data = request.get_json()
        if not data:
            return error("请提供注册信息")
        email = (data.get("email") or "").strip().lower()
        password = data.get("password", "")
        nickname = data.get("nickname", "用户")
        if not validate_email(email):
            return error("邮箱格式不正确")
        valid, msg = validate_password(password)
        if not valid:
            return error(msg)
        if User.query.filter_by(email=email).first():
            return error("该邮箱已注册，请直接登录")
        user = User(
            uuid=str(_uuid.uuid4()),
            email=email,
            nickname=nickname.strip()[:50] if nickname else "用户",
            role="user",
            credits_left=300,
        )
        user.set_password(password)
        user.start_trial(config.TRIAL_DAYS)
        db.session.add(user)
        db.session.commit()
        track_register(user.id)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return success({
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }, "注册成功")

    @bp.route("/login", methods=["POST"])
    @limiter.limit("20 per hour")
    def login():
        data = request.get_json()
        if not data:
            return error("请提供登录信息")
        email = (data.get("email") or "").strip().lower()
        password = data.get("password", "")
        if not email or not password:
            return error("请输入邮箱和密码")
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return error("邮箱或密码错误", 401)
        if not user.is_active:
            return error("账号已被禁用", 403)
        user.last_login_at = datetime.now(timezone.utc)
        user.login_count = (user.login_count or 0) + 1
        db.session.commit()
        track_login(user.id)
        sub = user.get_active_subscription()
        plan = user.get_current_plan()
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return success({
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "subscription": sub.to_dict() if sub else None,
            "plan": plan.to_dict() if plan else None,
        }, "登录成功")

    @bp.route("/login/code", methods=["POST"])
    @limiter.limit("10 per hour")
    def login_with_code():
        data = request.get_json()
        if not data:
            return error("请提供登录信息")
        target = (data.get("target") or "").strip().lower()
        code = (data.get("code") or "").strip()
        if not target or not code:
            return error("请输入邮箱/手机号和验证码")
        vc = VerifyCode.query.filter_by(
            target=target, purpose="login", used=False
        ).order_by(VerifyCode.created_at.desc()).first()
        if not vc:
            return error("验证码不存在或已过期")
        if datetime.now(timezone.utc) > vc.expires_at:
            vc.used = True
            db.session.commit()
            return error("验证码已过期")
        if vc.attempts >= 5:
            vc.used = True
            db.session.commit()
            return error("错误次数过多")
        if vc.code != code:
            vc.attempts += 1
            db.session.commit()
            remaining = 5 - vc.attempts
            return error(f"验证码错误，还可尝试 {remaining} 次")
        vc.used = True
        db.session.commit()
        user = User.query.filter(
            (User.email == target) | (User.phone == target)
        ).first()
        if not user:
            return error("账号不存在，请先注册")
        user.last_login_at = datetime.now(timezone.utc)
        user.login_count = (user.login_count or 0) + 1
        db.session.commit()
        track_login(user.id)
        access_token = create_access_token(identity=str(user.id))
        return success({
            "user": user.to_dict(),
            "access_token": access_token,
        }, "登录成功")

    @bp.route("/me", methods=["GET"])
    @jwt_required_custom()
    def me(**kwargs):
        current_user = kwargs["current_user"]
        sub = current_user.get_active_subscription()
        plan = current_user.get_current_plan()
        return success({
            "user": current_user.to_dict(),
            "subscription": sub.to_dict() if sub else None,
            "plan": plan.to_dict() if plan else None,
        })

    @bp.route("/forgot-password", methods=["POST"])
    @limiter.limit("5 per hour")
    def forgot_password():
        data = request.get_json()
        email = (data.get("email") or "").strip().lower() if data else ""
        if not validate_email(email):
            return error("请输入正确的邮箱")
        user = User.query.filter_by(email=email).first()
        if not user:
            return success(message="如果该邮箱已注册，您将收到重置密码的验证码")
        import random
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        now = datetime.now(timezone.utc)
        VerifyCode.query.filter_by(target=email, purpose="reset_password", used=False).update({"used": True})
        vc = VerifyCode(target=email, code=code, purpose="reset_password",
                        created_at=now, expires_at=now + timedelta(minutes=10))
        db.session.add(vc)
        db.session.commit()
        send_email_code(email, code, purpose="login")
        return success(message="如果该邮箱已注册，您将收到重置密码的验证码")

    @bp.route("/reset-password", methods=["POST"])
    @limiter.limit("10 per hour")
    def reset_password():
        data = request.get_json()
        if not data:
            return error("请提供重置信息")
        email = (data.get("email") or "").strip().lower()
        code = (data.get("code") or "").strip()
        new_password = data.get("new_password", "")
        if not email or not code:
            return error("请提供邮箱和验证码")
        valid, msg = validate_password(new_password)
        if not valid:
            return error(msg)
        vc = VerifyCode.query.filter_by(
            target=email, purpose="reset_password", used=False
        ).order_by(VerifyCode.created_at.desc()).first()
        if not vc or datetime.now(timezone.utc) > vc.expires_at or vc.code != code:
            return error("验证码无效或已过期")
        vc.used = True
        user = User.query.filter_by(email=email).first()
        if not user:
            return error("用户不存在")
        user.set_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return success(message="密码重置成功，请使用新密码登录")

    @bp.route("/verify-email/send", methods=["POST"])
    @jwt_required_custom()
    @limiter.limit("5 per hour")
    def send_verify_email(**kwargs):
        current_user = kwargs["current_user"]
        if not current_user.email:
            return error("请先绑定邮箱")
        if current_user.email_verified:
            return error("邮箱已验证")
        import random
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        now = datetime.now(timezone.utc)
        VerifyCode.query.filter_by(target=current_user.email, purpose="verify_email", used=False).update({"used": True})
        vc = VerifyCode(target=current_user.email, code=code, purpose="verify_email",
                        created_at=now, expires_at=now + timedelta(minutes=10))
        db.session.add(vc)
        db.session.commit()
        send_email_code(current_user.email, code, purpose="bind")
        return success(message="验证邮件已发送")

    @bp.route("/verify-email/confirm", methods=["POST"])
    @jwt_required_custom()
    def confirm_verify_email(**kwargs):
        current_user = kwargs["current_user"]
        data = request.get_json()
        code = (data.get("code") or "").strip() if data else ""
        if not code:
            return error("请输入验证码")
        vc = VerifyCode.query.filter_by(
            target=current_user.email, purpose="verify_email", used=False
        ).order_by(VerifyCode.created_at.desc()).first()
        if not vc or datetime.now(timezone.utc) > vc.expires_at or vc.code != code:
            return error("验证码无效或已过期")
        vc.used = True
        current_user.email_verified = True
        current_user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return success(message="邮箱验证成功")

    return bp
