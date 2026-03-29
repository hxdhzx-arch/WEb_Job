"""
models/subscription.py — 订阅模型
"""
from datetime import datetime, timezone
from backend.extensions import db


class Subscription(db.Model):
    __tablename__ = "saas_subscriptions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("saas_plans.id"), nullable=False)

    billing_cycle = db.Column(db.String(20), nullable=False, default="monthly",
                              comment="monthly / yearly")
    status = db.Column(db.String(20), nullable=False, default="active",
                       comment="active / expired / cancelled / trial / past_due")

    current_period_start = db.Column(db.DateTime(timezone=True), nullable=False,
                                     default=lambda: datetime.now(timezone.utc))
    current_period_end = db.Column(db.DateTime(timezone=True), nullable=False)

    # 第三方支付关联
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    alipay_agreement_no = db.Column(db.String(100), nullable=True)

    auto_renew = db.Column(db.Boolean, default=True)
    cancelled_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    @property
    def is_active(self) -> bool:
        if self.status != "active":
            return False
        return datetime.now(timezone.utc) < self.current_period_end

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.current_period_end

    @property
    def days_until_expiry(self) -> int:
        delta = self.current_period_end - datetime.now(timezone.utc)
        return max(0, delta.days)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_id": self.plan_id,
            "plan_name": self.plan.display_name if self.plan else None,
            "billing_cycle": self.billing_cycle,
            "status": self.status,
            "current_period_start": self.current_period_start.isoformat() if self.current_period_start else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "auto_renew": self.auto_renew,
            "days_until_expiry": self.days_until_expiry,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Subscription {self.id} user={self.user_id} status={self.status}>"
