"""
analytics_tracker.py — 埋点追踪工具
"""
from datetime import datetime, timezone


def track_event(event_type: str, user_id=None, data=None):
    """
    记录埋点事件到数据库
    延迟导入避免循环依赖
    """
    from backend.models.analytics import AnalyticsEvent
    from backend.extensions import db

    event = AnalyticsEvent(
        event_type=event_type,
        user_id=user_id,
        data=data or {},
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(event)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


def track_register(user_id):
    track_event("register", user_id=user_id)


def track_login(user_id):
    track_event("login", user_id=user_id)


def track_subscribe(user_id, plan_name, billing_cycle):
    track_event("subscribe", user_id=user_id, data={
        "plan": plan_name,
        "billing_cycle": billing_cycle,
    })


def track_payment(user_id, amount, plan_name):
    track_event("payment", user_id=user_id, data={
        "amount": str(amount),
        "plan": plan_name,
    })


def track_churn(user_id, reason=None):
    track_event("churn", user_id=user_id, data={"reason": reason or ""})


def track_trial_start(user_id):
    track_event("trial_start", user_id=user_id)


def track_trial_convert(user_id, plan_name):
    track_event("trial_convert", user_id=user_id, data={"plan": plan_name})
