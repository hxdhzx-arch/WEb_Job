"""
models/promo.py — 优惠码 / 邀请码
"""
from datetime import datetime, timezone
from backend.extensions import db


class PromoCode(db.Model):
    __tablename__ = "saas_promo_codes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)

    type = db.Column(db.String(20), nullable=False, default="discount",
                     comment="discount / referral / trial_extend / credits")
    discount_percent = db.Column(db.Integer, default=0,
                                 comment="折扣率 (1-100), 如 20 = 8折")
    discount_amount = db.Column(db.Numeric(10, 2), default=0,
                                comment="固定减免金额")
    extra_credits = db.Column(db.Integer, default=0,
                              comment="赠送算力")
    extra_trial_days = db.Column(db.Integer, default=0,
                                 comment="延长试用天数")

    # 限制
    max_uses = db.Column(db.Integer, default=0, comment="最大使用次数, 0=无限")
    used_count = db.Column(db.Integer, default=0)
    applicable_plans = db.Column(db.JSON, nullable=True,
                                 comment='适用的套餐名列表 ["pro","enterprise"]')

    valid_from = db.Column(db.DateTime(timezone=True), nullable=True)
    valid_to = db.Column(db.DateTime(timezone=True), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # 创建者
    created_by = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    # 关系
    usages = db.relationship("PromoUsage", backref="promo_code", lazy="dynamic")

    @property
    def is_valid(self) -> bool:
        now = datetime.now(timezone.utc)
        if not self.is_active:
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True

    def calculate_discount(self, original_price: float) -> float:
        """计算折后价"""
        price = original_price
        if self.discount_percent > 0:
            price = price * (100 - self.discount_percent) / 100
        if self.discount_amount > 0:
            price = max(0, price - float(self.discount_amount))
        return round(price, 2)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "type": self.type,
            "discount_percent": self.discount_percent,
            "discount_amount": float(self.discount_amount or 0),
            "extra_credits": self.extra_credits,
            "extra_trial_days": self.extra_trial_days,
            "max_uses": self.max_uses,
            "used_count": self.used_count,
            "is_valid": self.is_valid,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
        }


class PromoUsage(db.Model):
    """优惠码使用记录"""
    __tablename__ = "saas_promo_usages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    promo_code_id = db.Column(db.Integer, db.ForeignKey("saas_promo_codes.id"),
                              nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"),
                        nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("saas_orders.id"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("promo_code_id", "user_id", name="uq_promo_user"),
    )
