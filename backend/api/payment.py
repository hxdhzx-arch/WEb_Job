"""
api/payment.py — 支付接口
"""
import json as _json
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request
from backend.extensions import db
from backend.models.order import Order, PaymentRecord
from backend.models.plan import Plan
from backend.models.subscription import Subscription
from backend.models.promo import PromoCode, PromoUsage
from backend.middleware.auth_required import jwt_required_custom
from backend.utils.response import success, error
from backend.utils.analytics_tracker import track_payment
import config


def create_blueprint():
    bp = Blueprint("payment", __name__, url_prefix="/payment")

    @bp.route("/create-order", methods=["POST"])
    @jwt_required_custom()
    def create_order(**kwargs):
        current_user = kwargs["current_user"]
        data = request.get_json()
        if not data:
            return error("请提供订单信息")
        plan_id = data.get("plan_id")
        billing_cycle = data.get("billing_cycle", "monthly")
        promo_code_str = data.get("promo_code", "").strip()
        plan = Plan.query.get(plan_id)
        if not plan or not plan.is_active:
            return error("套餐不存在")
        if plan.name == "free":
            return error("免费套餐无需支付")
        original_price = float(plan.price_yearly or 0) if billing_cycle == "yearly" else float(plan.price_monthly or 0)
        final_price = original_price
        discount_amount = 0
        promo = None
        if promo_code_str:
            promo = PromoCode.query.filter_by(code=promo_code_str.upper()).first()
            if not promo or not promo.is_valid:
                return error("优惠码无效或已过期")
            used = PromoUsage.query.filter_by(promo_code_id=promo.id, user_id=current_user.id).first()
            if used:
                return error("您已使用过该优惠码")
            if promo.applicable_plans and plan.name not in promo.applicable_plans:
                return error("该优惠码不适用于此套餐")
            final_price = promo.calculate_discount(original_price)
            discount_amount = original_price - final_price
        order = Order(user_id=current_user.id, plan_id=plan.id,
                      billing_cycle=billing_cycle, original_amount=original_price,
                      amount=final_price, currency=plan.currency,
                      discount_amount=discount_amount,
                      promo_code_id=promo.id if promo else None, status="pending")
        db.session.add(order)
        db.session.commit()
        return success({"order": order.to_dict(), "payment_methods": _get_available_methods()}, "订单创建成功")

    @bp.route("/order/<order_no>", methods=["GET"])
    @jwt_required_custom()
    def get_order(order_no, **kwargs):
        current_user = kwargs["current_user"]
        order = Order.query.filter_by(order_no=order_no, user_id=current_user.id).first()
        if not order:
            return error("订单不存在", 404)
        payments = [p.to_dict() for p in order.payments.all()]
        return success({"order": order.to_dict(), "payments": payments})

    @bp.route("/webhook/stripe", methods=["POST"])
    def stripe_webhook():
        return success(message="webhook received")

    @bp.route("/webhook/alipay", methods=["POST"])
    def alipay_webhook():
        return success(message="webhook received")

    @bp.route("/webhook/wechat", methods=["POST"])
    def wechat_webhook():
        return success(message="webhook received")

    @bp.route("/simulate-pay", methods=["POST"])
    @jwt_required_custom()
    def simulate_payment(**kwargs):
        current_user = kwargs["current_user"]
        data = request.get_json()
        order_no = data.get("order_no") if data else None
        if not order_no:
            return error("请提供订单号")
        order = Order.query.filter_by(order_no=order_no, user_id=current_user.id).first()
        if not order:
            return error("订单不存在")
        if order.status == "paid":
            return error("订单已支付")
        now = datetime.now(timezone.utc)
        payment = PaymentRecord(order_id=order.id, payment_method="manual",
                                transaction_id=f"SIM_{order.order_no}",
                                amount=order.amount, currency=order.currency,
                                status="success",
                                raw_response=_json.dumps({"simulated": True}))
        db.session.add(payment)
        order.status = "paid"
        order.paid_at = now
        order.updated_at = now
        _activate_subscription(current_user, order, now)
        if order.promo_code_id:
            promo = PromoCode.query.get(order.promo_code_id)
            if promo:
                promo.used_count += 1
                usage = PromoUsage(promo_code_id=promo.id, user_id=current_user.id, order_id=order.id)
                db.session.add(usage)
        db.session.commit()
        track_payment(current_user.id, float(order.amount), order.plan.name if order.plan else "")
        sub = current_user.get_active_subscription()
        return success({"order": order.to_dict(),
                        "subscription": sub.to_dict() if sub else None}, "支付成功")

    return bp


def _activate_subscription(user, order, now):
    period_end = now + timedelta(days=365 if order.billing_cycle == "yearly" else 30)
    sub = Subscription.query.filter_by(user_id=user.id, status="active").first()
    if sub:
        sub.plan_id = order.plan_id
        sub.billing_cycle = order.billing_cycle
        sub.current_period_start = now
        sub.current_period_end = period_end
        sub.updated_at = now
    else:
        sub = Subscription(user_id=user.id, plan_id=order.plan_id,
                           billing_cycle=order.billing_cycle, status="active",
                           current_period_start=now, current_period_end=period_end)
        db.session.add(sub)
    order.subscription_id = sub.id


def _get_available_methods():
    methods = []
    if config.STRIPE_SECRET_KEY:
        methods.append({"id": "stripe", "name": "Stripe", "enabled": True})
    if config.ALIPAY_APP_ID:
        methods.append({"id": "alipay", "name": "支付宝", "enabled": True})
    if config.WECHAT_PAY_APP_ID:
        methods.append({"id": "wechat", "name": "微信支付", "enabled": True})
    if not methods:
        methods.append({"id": "manual", "name": "人工处理", "enabled": True})
    return methods
