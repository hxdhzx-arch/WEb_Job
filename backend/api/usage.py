"""
api/usage.py — 用量查询
"""
from flask import Blueprint, request
from backend.middleware.auth_required import jwt_required_custom
from backend.models.usage import UsageLog, get_daily_usage, get_monthly_usage
from backend.utils.response import success, paginated


def create_blueprint():
    bp = Blueprint("usage", __name__, url_prefix="/usage")

    @bp.route("/summary", methods=["GET"])
    @jwt_required_custom()
    def usage_summary(**kwargs):
        current_user = kwargs["current_user"]
        daily = get_daily_usage(current_user.id)
        monthly = get_monthly_usage(current_user.id)
        from backend.extensions import db
        from sqlalchemy import func
        from datetime import date
        today = date.today()
        first_day = today.replace(day=1)
        feature_stats = db.session.query(
            UsageLog.feature, func.count(UsageLog.id).label("count")
        ).filter(UsageLog.user_id == current_user.id,
                 func.date(UsageLog.created_at) >= first_day
        ).group_by(UsageLog.feature).all()
        return success({
            "daily_total": daily,
            "monthly_total": monthly,
            "by_feature": {f: c for f, c in feature_stats},
        })

    @bp.route("/logs", methods=["GET"])
    @jwt_required_custom()
    def usage_logs(**kwargs):
        current_user = kwargs["current_user"]
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        feature = request.args.get("feature")
        query = UsageLog.query.filter_by(user_id=current_user.id)
        if feature:
            query = query.filter_by(feature=feature)
        query = query.order_by(UsageLog.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [log.to_dict() for log in pagination.items]
        return paginated(items, pagination.total, page, per_page)

    return bp
