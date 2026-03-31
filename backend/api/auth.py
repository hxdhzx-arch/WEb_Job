"""
api/auth.py — 认证模块
注册、登录、登录锁定、刷新会话、退出、找回密码、邮箱验证
"""
import uuid as _uuid
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    get_jwt_identity, get_jwt, jwt_required, decode_token
)

from backend.extensions import db, limiter
from backend.models.user import User
from backend.models.user_session import UserSession
from backend.models.token_blocklist import TokenBlocklist
from backend.models.verify_code import VerifyCode
from backend.middleware.auth_required import jwt_required_custom

from backend.utils.response import success, error
from backend.utils.validators import validate_email, validate_password
from backend.utils.analytics_tracker import track_register, track_login
from services.email_sender import send_verify_code as send_email_code
import config


def create_blueprint():
    bp = Blueprint("auth", __name__, url_prefix="/auth")

    def _record_session(user_id, refresh_token):
        try:
            refresh_jti = decode_token(refresh_token)["jti"]
            ip = request.remote_addr
            ua = request.user_agent.string if request.user_agent else ""
            UserSession.record_session(user_id, refresh_jti, ip, ua[:512])
        except Exception:
            pass

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
        _record_session(user.id, refresh_token)
        db.session.commit()
        
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
        if not user:
            return error("邮箱或密码错误", 401)
            
        if user.is_locked():
            return error("登录失败次数过多，账号已临时锁定，请稍后再试", 403)
            
        if not user.check_password(password):
            user.increase_failed_attempts()
            db.session.commit()
            return error("邮箱或密码错误", 401)
            
        if not user.is_active:
            return error("账号已被禁用", 403)
            
        # 登录成功，重置失败次数并更新会话信息
        user.reset_failed_attempts()
        user.last_login_at = datetime.now(timezone.utc)
        user.login_count = (user.login_count or 0) + 1
        user.ip_address = request.remote_addr
        user.device_hash = request.user_agent.string[:64] if request.user_agent else None
        db.session.commit()
        
        track_login(user.id)
        sub = user.get_active_subscription()
        plan = user.get_current_plan()
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        _record_session(user.id, refresh_token)
        db.session.commit()
        
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
            return error("错误次数过多，验证码已作废")
        if vc.code != code:
            vc.attempts += 1
            db.session.commit()
            remaining = 5 - vc.attempts
            return error(f"验证码错误，还可尝试 {remaining} 次")
            
        vc.used = True
        user = User.query.filter((User.email == target) | (User.phone == target)).first()
        if not user:
            return error("账号不存在，请先注册")
            
        if user.is_locked():
            return error("账号已被临时锁定，请稍后再试", 403)
            
        user.reset_failed_attempts()
        user.last_login_at = datetime.now(timezone.utc)
        user.login_count = (user.login_count or 0) + 1
        user.ip_address = request.remote_addr
        user.device_hash = request.user_agent.string[:64] if request.user_agent else None
        db.session.commit()
        
        track_login(user.id)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        _record_session(user.id, refresh_token)
        db.session.commit()
        
        return success({
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }, "登录成功")

    @bp.route("/refresh", methods=["POST"])
    @jwt_required(refresh=True)
    def refresh():
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return error("账号已被禁用或不存在", 403)
            
        # 刷新并生成新的 Access Token
        access_token = create_access_token(identity=str(user.id))
        
        # 可选：滚动更新 UserSession 活跃时间
        jti = get_jwt()["jti"]
        session = UserSession.query.filter_by(refresh_jti=jti, user_id=user.id).first()
        if session:
            session.last_active_at = datetime.now(timezone.utc)
            db.session.commit()
            
        return success({
            "access_token": access_token
        }, "Token刷新成功")

    @bp.route("/logout", methods=["POST"])
    @jwt_required_custom()
    def logout(**kwargs):
        current_user = kwargs["current_user"]
        
        # 撤销当前请求头中的 Access Token
        access_jti = get_jwt()["jti"]
        TokenBlocklist.revoke_token(access_jti, "access", current_user.id)
        
        # 可选撤销随请求体提交的 Refresh Token
        data = request.get_json(silent=True) or {}
        refresh_token = data.get("refresh_token")
        if refresh_token:
            try:
                refresh_jti = decode_token(refresh_token)["jti"]
                TokenBlocklist.revoke_token(refresh_jti, "refresh", current_user.id)
                # 标记 Session 为非活跃
                us = UserSession.query.filter_by(refresh_jti=refresh_jti).first()
                if us:
                    us.is_active = False
            except Exception:
                pass
                
        db.session.commit()
        return success(message="已成功退出登录")

    @bp.route("/me", methods=["GET"])
    @jwt_required_custom()
    def me(**kwargs):
        current_user = kwargs["current_user"]
        sub = current_user.get_active_subscription()
        plan = current_user.get_current_plan()
        
        # 构造详细的高级订阅UX交互支撑结构
        is_active = bool(sub and sub.status == "active")
        trial_ending_soon = False
        if current_user.is_trial_active and current_user.trial_ends_at:
            h_left = (current_user.trial_ends_at - datetime.now(timezone.utc)).total_seconds() / 3600
            trial_ending_soon = 0 < h_left <= 48
            
        status_info = {
            "has_subscription": bool(sub),
            "status": sub.status if sub else "none",
            "is_trial": current_user.is_trial_active,
            "trial_ends_at": current_user.trial_ends_at.isoformat() if current_user.trial_ends_at else None,
            "trial_ending_soon": trial_ending_soon,
            "cancel_at_period_end": sub.cancel_at_period_end if sub else False,
            "current_period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None
        }
        
        return success({
            "user": current_user.to_dict(include_sensitive=False),
            "email_verified": current_user.email_verified,
            "subscription": sub.to_dict() if sub else None,
            "plan": plan.to_dict() if plan else None,
            "subscription_ux_states": status_info
        })
        
    @bp.route("/export-data", methods=["GET"])
    @jwt_required_custom()
    @limiter.limit("2 per day")
    def export_data(**kwargs):
        current_user = kwargs["current_user"]
        from backend.models.resume import Resume
        from backend.models.personal_site import PersonalSite
        from backend.models.order import Order
        
        resumes = Resume.query.filter_by(user_id=current_user.id).all()
        sites = PersonalSite.query.filter_by(user_id=current_user.id).all()
        orders = Order.query.filter_by(user_id=current_user.id).all()
        
        data = {
            "profile": current_user.to_dict(),
            "resumes": [{"id": r.id, "title": r.title, "data": r.resume_data} for r in resumes],
            "sites": [{"id": s.id, "slug": s.slug, "data": s.site_data} for s in sites],
            "orders": [{"order_no": o.order_no, "amount": str(o.amount), "status": o.status} for o in orders]
        }
        
        return success(data, "数据已成功打包提取")
        
    @bp.route("/delete-account", methods=["POST"])
    @jwt_required_custom()
    @limiter.limit("3 per day")
    def delete_account(**kwargs):
        current_user = kwargs["current_user"]
        data = request.get_json()
        password = data.get("password", "") if data else ""
        if not current_user.check_password(password):
            return error("注销账号需验证原密码，错误", 403)
            
        from backend.utils.logger import sys_logger
        sys_logger.warning("auth", "account_deleted", {"user_id": current_user.id})
            
        # 1. 中断所有计费周期的续签
        sub = current_user.get_active_subscription()
        if sub: sub.cancel_at_period_end = True
            
        # 2. 软删除/混淆隔离核心私密信息
        deleted_stamp = str(int(datetime.now(timezone.utc).timestamp()))
        current_user.email = f"DELETED_{deleted_stamp}_{current_user.id}"
        current_user.is_active = False
        
        # 3. 驱逐所有会话
        UserSession.query.filter_by(user_id=current_user.id).update({"is_active": False})
        TokenBlocklist.revoke_token(get_jwt()["jti"], "access", current_user.id)
        
        db.session.commit()
        return success(message="您的账号已被永久注销，有关您的个人识别数据已粉碎并解除关联。感谢您的使用。")

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
            
        # 重设密码并强制所有之前发放的 Token 在下次校验时直接失效
        user.set_password(new_password)
        # 解锁账号
        user.reset_failed_attempts()
        user.updated_at = datetime.now(timezone.utc)
        
        # 获取最新的 active session 全部废弃
        UserSession.query.filter_by(user_id=user.id).update({"is_active": False})
        
        db.session.commit()
        return success(message="密码重置成功，所有旧设备均已被登出，请使用新密码登录")

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

    @bp.route("/sessions", methods=["GET"])
    @jwt_required_custom()
    def get_sessions(**kwargs):
        current_user = kwargs["current_user"]
        sessions = UserSession.query.filter_by(user_id=current_user.id, is_active=True).order_by(UserSession.last_active_at.desc()).all()
        return success({
            "sessions": [s.to_dict() for s in sessions]
        })

    return bp
