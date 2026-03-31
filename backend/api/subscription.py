"""
api/subscription.py — 订阅管理
"""
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request
from backend.extensions import db
from backend.models.subscription import Subscription
from backend.models.plan import Plan
from backend.middleware.auth_required import jwt_required_custom
from backend.utils.response import success, error
from backend.utils.analytics_tracker import track_subscribe


def create_blueprint():
    bp = Blueprint("subscription", __name__, url_prefix="/subscription")

    @bp.route("/create", methods=["POST"])
    @jwt_required_custom()
    def create_subscription(**kwargs):
        current_user = kwargs["current_user"]
        
        # 安全修复：禁止通过 API 直接伪造订阅状态
        import os
        if os.getenv("FLASK_ENV") == "production":
            return error("生产环境安全限制：禁止越过真实支付闭环直接强制激活订阅。请回到原页面进行支付。")

        data = request.get_json()
        if not data:
            return error("请选择套餐")
        plan_id = data.get("plan_id")
        billing_cycle = data.get("billing_cycle", "monthly")
        if billing_cycle not in ("monthly", "yearly"):
            return error("billing_cycle 必须是 monthly 或 yearly")
        plan = Plan.query.get(plan_id)
        if not plan or not plan.is_active:
            return error("套餐不存在")
        if plan.name == "free":
            return error("免费套餐无需订阅")
        existing = Subscription.query.filter_by(user_id=current_user.id, status="active").first()
        now = datetime.now(timezone.utc)
        period_end = now + timedelta(days=30 if billing_cycle == "monthly" else 365)
        if existing:
            existing.plan_id = plan.id
            existing.billing_cycle = billing_cycle
            existing.status = "active"
            existing.current_period_start = now
            existing.current_period_end = period_end
            existing.updated_at = now
            sub = existing
        else:
            sub = Subscription(user_id=current_user.id, plan_id=plan.id,
                               billing_cycle=billing_cycle, status="active",
                               current_period_start=now, current_period_end=period_end)
            db.session.add(sub)
        db.session.commit()
        track_subscribe(current_user.id, plan.name, billing_cycle)
        return success(sub.to_dict(), "订阅成功")

    @bp.route("/cancel", methods=["POST"])
    @jwt_required_custom()
    def cancel_subscription(**kwargs):
        current_user = kwargs["current_user"]
        sub = Subscription.query.filter_by(user_id=current_user.id, status="active").first()
        if not sub:
            return error("没有活跃的订阅")
        sub.auto_renew = False
        sub.cancelled_at = datetime.now(timezone.utc)
        sub.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return success(sub.to_dict(), "已取消自动续费，服务将在当前周期结束后停止")

    @bp.route("/reactivate", methods=["POST"])
    @jwt_required_custom()
    def reactivate_subscription(**kwargs):
        current_user = kwargs["current_user"]
        sub = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.updated_at.desc()).first()
        if not sub:
            return error("没有找到订阅记录")
        if sub.status == "active" and sub.auto_renew:
            return error("订阅已处于激活状态")
        now = datetime.now(timezone.utc)
        if sub.is_expired:
            period_end = now + timedelta(days=30 if sub.billing_cycle == "monthly" else 365)
            sub.current_period_start = now
            sub.current_period_end = period_end
        sub.status = "active"
        sub.auto_renew = True
        sub.cancelled_at = None
        sub.updated_at = now
        db.session.commit()
        return success(sub.to_dict(), "订阅已重新激活")

    return bp
