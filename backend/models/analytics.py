"""
models/analytics.py — 埋点事件模型
"""
from datetime import datetime, timezone
from backend.extensions import db


class AnalyticsEvent(db.Model):
    __tablename__ = "saas_analytics_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_type = db.Column(db.String(50), nullable=False, index=True,
                           comment="register / login / subscribe / payment / churn / trial_start / ...")
    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=True, index=True)
    data = db.Column(db.JSON, default=dict, comment="事件详情")

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
