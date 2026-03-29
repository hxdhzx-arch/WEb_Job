"""
models/order.py — 订单 + 支付记录
"""
import uuid as _uuid
from datetime import datetime, timezone
from backend.extensions import db


def _gen_order_no():
    """生成唯一订单号: ORD + 时间戳 + 随机"""
    now = datetime.now(timezone.utc)
    return "ORD" + now.strftime("%Y%m%d%H%M%S") + _uuid.uuid4().hex[:8].upper()


class Order(db.Model):
    __tablename__ = "saas_orders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(32), unique=True, nullable=False,
                         default=_gen_order_no, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("saas_plans.id"), nullable=False)

    billing_cycle = db.Column(db.String(20), nullable=False, default="monthly")
    original_amount = db.Column(db.Numeric(10, 2), nullable=False, comment="原价")
    amount = db.Column(db.Numeric(10, 2), nullable=False, comment="实付金额")
    currency = db.Column(db.String(10), default="CNY")

    # 优惠码
    promo_code_id = db.Column(db.Integer, db.ForeignKey("saas_promo_codes.id"), nullable=True)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)

    status = db.Column(db.String(20), nullable=False, default="pending",
                       comment="pending / paid / failed / refunded / cancelled")
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # 关联的订阅 (支付成功后创建)
    subscription_id = db.Column(db.Integer, db.ForeignKey("saas_subscriptions.id"), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    payments = db.relationship("PaymentRecord", backref="order", lazy="dynamic")
    plan = db.relationship("Plan", backref="orders")

    def to_dict(self):
        return {
            "id": self.id,
            "order_no": self.order_no,
            "user_id": self.user_id,
            "plan_id": self.plan_id,
            "plan_name": self.plan.display_name if self.plan else None,
            "billing_cycle": self.billing_cycle,
            "original_amount": float(self.original_amount or 0),
            "amount": float(self.amount or 0),
            "currency": self.currency,
            "discount_amount": float(self.discount_amount or 0),
            "status": self.status,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Order {self.order_no} status={self.status}>"


class PaymentRecord(db.Model):
    __tablename__ = "saas_payment_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("saas_orders.id"), nullable=False, index=True)

    payment_method = db.Column(db.String(20), nullable=False,
                               comment="stripe / alipay / wechat / manual")
    transaction_id = db.Column(db.String(200), nullable=True, comment="第三方交易号")
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default="CNY")

    status = db.Column(db.String(20), nullable=False, default="pending",
                       comment="pending / success / failed / refunded")
    raw_response = db.Column(db.Text, nullable=True, comment="原始支付回调数据 JSON")

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "payment_method": self.payment_method,
            "transaction_id": self.transaction_id,
            "amount": float(self.amount or 0),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<PaymentRecord {self.id} method={self.payment_method}>"
