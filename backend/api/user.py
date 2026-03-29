"""
api/user.py — 用户信息管理
"""
from datetime import datetime, timezone
from flask import Blueprint, request
from backend.extensions import db
from backend.middleware.auth_required import jwt_required_custom
from backend.models.usage import get_daily_usage, get_monthly_usage, UsageLog
from backend.utils.response import success, error
from backend.utils.validators import validate_password, validate_nickname


def create_blueprint():
    bp = Blueprint("user", __name__, url_prefix="/user")

    @bp.route("/profile", methods=["PUT"])
    @jwt_required_custom()
    def update_profile(**kwargs):
        current_user = kwargs["current_user"]
        data = request.get_json()
        if not data:
            return error("请提供更新信息")
        if "nickname" in data:
            valid, msg = validate_nickname(data["nickname"])
            if not valid:
                return error(msg)
            current_user.nickname = data["nickname"].strip()[:50]
        if "avatar_url" in data:
            current_user.avatar_url = (data["avatar_url"] or "")[:500]
        current_user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return success(current_user.to_dict(), "资料更新成功")

    @bp.route("/password", methods=["PUT"])
    @jwt_required_custom()
    def change_password(**kwargs):
        current_user = kwargs["current_user"]
        data = request.get_json()
        if not data:
            return error("请提供密码信息")
        old_password = data.get("old_password", "")
        new_password = data.get("new_password", "")
        if current_user.password_hash and not current_user.check_password(old_password):
            return error("旧密码错误")
        valid, msg = validate_password(new_password)
        if not valid:
            return error(msg)
        current_user.set_password(new_password)
        current_user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return success(message="密码修改成功")

    @bp.route("/subscription", methods=["GET"])
    @jwt_required_custom()
    def get_subscription(**kwargs):
        current_user = kwargs["current_user"]
        sub = current_user.get_active_subscription()
        plan = current_user.get_current_plan()
        return success({
            "subscription": sub.to_dict() if sub else None,
            "plan": plan.to_dict() if plan else None,
            "is_trial": current_user.is_trial_active,
            "trial_ends_at": current_user.trial_ends_at.isoformat() if current_user.trial_ends_at else None,
        })

    @bp.route("/usage", methods=["GET"])
    @jwt_required_custom()
    def get_usage(**kwargs):
        current_user = kwargs["current_user"]
        plan = current_user.get_current_plan()
        daily = get_daily_usage(current_user.id)
        monthly = get_monthly_usage(current_user.id)
        return success({
            "daily_used": daily,
            "monthly_used": monthly,
            "daily_limit": plan.max_ai_calls_daily if plan else 5,
            "monthly_limit": plan.max_ai_calls_monthly if plan else 100,
            "credits_left": current_user.credits_left,
        })

    @bp.route("/usage/daily", methods=["GET"])
    @jwt_required_custom()
    def get_daily_detail(**kwargs):
        current_user = kwargs["current_user"]
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        query = UsageLog.query.filter_by(user_id=current_user.id).order_by(UsageLog.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [log.to_dict() for log in pagination.items]
        from backend.utils.response import paginated
        return paginated(items, pagination.total, page, per_page)

    return bp
