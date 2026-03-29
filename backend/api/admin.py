"""
api/admin.py — 后台管理 API
"""
import csv
import io
from datetime import datetime, timezone, timedelta, date
from flask import Blueprint, request, Response
from backend.extensions import db
from backend.models.user import User
from backend.models.subscription import Subscription
from backend.models.order import Order
from backend.models.usage import UsageLog
from backend.models.plan import Plan
from backend.models.error_log import ErrorLog
from backend.models.contact_lead import ContactLead
from backend.models.analytics import AnalyticsEvent
from backend.middleware.auth_required import admin_required
from backend.utils.response import success, error, paginated
from sqlalchemy import func


def create_blueprint():
    bp = Blueprint("admin", __name__, url_prefix="/admin")

    @bp.route("/users", methods=["GET"])
    @admin_required()
    def list_users(**kwargs):
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        search = request.args.get("search", "").strip()
        role = request.args.get("role")
        query = User.query
        if search:
            like = f"%{search}%"
            query = query.filter(
                (User.email.ilike(like)) | (User.phone.ilike(like)) |
                (User.nickname.ilike(like)) | (User.uuid.ilike(like))
            )
        if role:
            query = query.filter_by(role=role)
        query = query.order_by(User.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [u.to_dict(include_sensitive=True) for u in pagination.items]
        return paginated(items, pagination.total, page, per_page)

    @bp.route("/users/<int:user_id>", methods=["GET"])
    @admin_required()
    def get_user(user_id, **kwargs):
        user = User.query.get(user_id)
        if not user:
            return error("用户不存在", 404)
        sub = user.get_active_subscription()
        plan = user.get_current_plan()
        return success({
            "user": user.to_dict(include_sensitive=True),
            "subscription": sub.to_dict() if sub else None,
            "plan": plan.to_dict() if plan else None,
        })

    @bp.route("/users/<int:user_id>/plan", methods=["PUT"])
    @admin_required()
    def update_user_plan(user_id, **kwargs):
        user = User.query.get(user_id)
        if not user:
            return error("用户不存在", 404)
        data = request.get_json()
        plan_id = data.get("plan_id") if data else None
        days = data.get("days", 30) if data else 30
        if not plan_id:
            return error("请指定套餐")
        plan = Plan.query.get(plan_id)
        if not plan:
            return error("套餐不存在")
        now = datetime.now(timezone.utc)
        sub = Subscription.query.filter_by(user_id=user.id, status="active").first()
        if sub:
            sub.plan_id = plan.id
            sub.current_period_start = now
            sub.current_period_end = now + timedelta(days=days)
            sub.updated_at = now
        else:
            sub = Subscription(user_id=user.id, plan_id=plan.id,
                               billing_cycle="monthly", status="active",
                               current_period_start=now,
                               current_period_end=now + timedelta(days=days))
            db.session.add(sub)
        db.session.commit()
        return success(sub.to_dict(), "套餐已调整")

    @bp.route("/users/<int:user_id>/credits", methods=["PUT"])
    @admin_required()
    def update_user_credits(user_id, **kwargs):
        user = User.query.get(user_id)
        if not user:
            return error("用户不存在", 404)
        data = request.get_json()
        if not data:
            return error("请提供额度信息")
        action = data.get("action", "set")
        amount = data.get("amount", 0)
        if action == "set":
            user.credits_left = max(0, amount)
        elif action == "add":
            user.credits_left = max(0, user.credits_left + amount)
        elif action == "deduct":
            user.credits_left = max(0, user.credits_left - amount)
        else:
            return error("action 必须是 set / add / deduct")
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return success({"credits_left": user.credits_left}, "额度已调整")

    @bp.route("/subscriptions", methods=["GET"])
    @admin_required()
    def list_subscriptions(**kwargs):
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        status = request.args.get("status")
        query = Subscription.query
        if status:
            query = query.filter_by(status=status)
        query = query.order_by(Subscription.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [s.to_dict() for s in pagination.items]
        return paginated(items, pagination.total, page, per_page)

    @bp.route("/orders", methods=["GET"])
    @admin_required()
    def list_orders(**kwargs):
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        status = request.args.get("status")
        query = Order.query
        if status:
            query = query.filter_by(status=status)
        query = query.order_by(Order.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [o.to_dict() for o in pagination.items]
        return paginated(items, pagination.total, page, per_page)

    @bp.route("/usage/stats", methods=["GET"])
    @admin_required()
    def usage_stats(**kwargs):
        days = request.args.get("days", 30, type=int)
        cutoff = date.today() - timedelta(days=days)
        daily_stats = db.session.query(
            func.date(UsageLog.created_at).label("d"),
            func.count(UsageLog.id).label("c"),
        ).filter(func.date(UsageLog.created_at) >= cutoff).group_by(
            func.date(UsageLog.created_at)).order_by(func.date(UsageLog.created_at)).all()
        feature_stats = db.session.query(
            UsageLog.feature, func.count(UsageLog.id).label("c"),
        ).filter(func.date(UsageLog.created_at) >= cutoff).group_by(UsageLog.feature).all()
        return success({
            "daily": [{"date": str(d), "count": c} for d, c in daily_stats],
            "by_feature": {f: c for f, c in feature_stats},
            "total_calls": sum(c for _, c in daily_stats),
        })

    @bp.route("/analytics/overview", methods=["GET"])
    @admin_required()
    def analytics_overview(**kwargs):
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        total_users = User.query.count()
        new_users_7d = User.query.filter(User.created_at >= seven_days_ago).count()
        new_users_30d = User.query.filter(User.created_at >= thirty_days_ago).count()
        active_subs = Subscription.query.filter_by(status="active").count()
        total_revenue = db.session.query(func.sum(Order.amount)).filter_by(status="paid").scalar() or 0
        paid_users = db.session.query(func.count(func.distinct(Order.user_id))).filter_by(status="paid").scalar() or 0
        conversion_rate = (paid_users / total_users * 100) if total_users > 0 else 0
        return success({
            "total_users": total_users, "new_users_7d": new_users_7d,
            "new_users_30d": new_users_30d, "active_subscriptions": active_subs,
            "total_revenue": float(total_revenue), "paid_users": paid_users,
            "conversion_rate": round(conversion_rate, 2),
        })

    @bp.route("/analytics/conversion", methods=["GET"])
    @admin_required()
    def analytics_conversion(**kwargs):
        days = request.args.get("days", 30, type=int)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        daily_reg = db.session.query(
            func.date(User.created_at).label("d"), func.count(User.id).label("c"),
        ).filter(User.created_at >= cutoff).group_by(func.date(User.created_at)).all()
        daily_pay = db.session.query(
            func.date(Order.paid_at).label("d"), func.count(Order.id).label("c"),
            func.sum(Order.amount).label("r"),
        ).filter(Order.status == "paid", Order.paid_at >= cutoff).group_by(func.date(Order.paid_at)).all()
        return success({
            "daily_registrations": [{"date": str(d), "count": c} for d, c in daily_reg],
            "daily_payments": [{"date": str(d), "count": c, "revenue": float(r or 0)} for d, c, r in daily_pay],
        })

    @bp.route("/analytics/churn", methods=["GET"])
    @admin_required()
    def analytics_churn(**kwargs):
        days = request.args.get("days", 30, type=int)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        churned = Subscription.query.filter(
            Subscription.status.in_(["expired", "cancelled"]),
            Subscription.updated_at >= cutoff).count()
        cancelled = Subscription.query.filter(Subscription.cancelled_at >= cutoff).count()
        inactive_users = User.query.filter(
            (User.last_login_at < cutoff) | (User.last_login_at.is_(None)),
            User.created_at < cutoff).count()
        return success({
            "churned_subscriptions": churned,
            "cancelled_subscriptions": cancelled,
            "inactive_users": inactive_users,
        })

    @bp.route("/errors", methods=["GET"])
    @admin_required()
    def list_errors(**kwargs):
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        level = request.args.get("level")
        query = ErrorLog.query
        if level:
            query = query.filter_by(level=level)
        query = query.order_by(ErrorLog.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [e.to_dict() for e in pagination.items]
        return paginated(items, pagination.total, page, per_page)

    @bp.route("/leads", methods=["GET"])
    @admin_required()
    def list_leads(**kwargs):
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        status = request.args.get("status")
        query = ContactLead.query
        if status:
            query = query.filter_by(status=status)
        query = query.order_by(ContactLead.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [lead.to_dict() for lead in pagination.items]
        return paginated(items, pagination.total, page, per_page)

    @bp.route("/leads/export", methods=["GET"])
    @admin_required()
    def export_leads(**kwargs):
        status = request.args.get("status")
        query = ContactLead.query
        if status:
            query = query.filter_by(status=status)
        leads = query.order_by(ContactLead.created_at.desc()).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "姓名", "邮箱", "手机", "公司", "留言", "来源", "状态", "创建时间"])
        for l in leads:
            writer.writerow([l.id, l.name, l.email, l.phone, l.company,
                             l.message, l.source, l.status,
                             l.created_at.isoformat() if l.created_at else ""])
        csv_content = output.getvalue()
        output.close()
        return Response(csv_content, mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=leads_export.csv",
                                 "Content-Type": "text/csv; charset=utf-8-sig"})

    return bp
