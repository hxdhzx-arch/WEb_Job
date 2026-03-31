"""
api/payment.py — Stripe 支付闭环实现
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
import stripe

# 初始化 Stripe
stripe.api_key = config.STRIPE_SECRET_KEY

def create_blueprint():
    bp = Blueprint("payment", __name__, url_prefix="/payment")

    @bp.route("/create-stripe-checkout", methods=["POST"])
    @jwt_required_custom()
    def create_stripe_checkout(**kwargs):
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
            
        # 1. 创建订单处于 pending 状态，不允许下发任何订阅权益
        order = Order(user_id=current_user.id, plan_id=plan.id,
                      billing_cycle=billing_cycle, original_amount=original_price,
                      amount=final_price, currency=plan.currency,
                      discount_amount=discount_amount,
                      promo_code_id=promo.id if promo else None, status="pending")
        db.session.add(order)
        db.session.flush() # 拿到 order.order_no
        
        # 2. 调用 Stripe Checkout 创建支付会话
        try:
            unit_amount = int(final_price * 100) # Stripe 需要最小货币单位 (e.g. 分/美分)
            domain_url = request.headers.get("Origin") or "http://localhost:5000"
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card', 'alipay', 'wechat_pay'],
                line_items=[{
                    'price_data': {
                        'currency': order.currency.lower(),
                        'product_data': {
                            'name': f"SaaS Pro 订阅 - {plan.display_name} ({billing_cycle})",
                        },
                        'unit_amount': unit_amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=domain_url + '/dashboard?payment=success&order_no=' + order.order_no,
                cancel_url=domain_url + '/dashboard?payment=cancelled',
                client_reference_id=str(current_user.id),
                metadata={'order_no': order.order_no}
            )
            db.session.commit()
            return success({
                "checkout_url": checkout_session.url,
                "order_no": order.order_no,
                "status": order.status
            })
        except Exception as e:
            db.session.rollback()
            return error(f"Stripe 接口异常: {str(e)}")

    @bp.route("/webhook/stripe", methods=["POST"])
    def stripe_webhook():
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get("Stripe-Signature", "")
        webhook_secret = config.STRIPE_WEBHOOK_SECRET
        
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError:
            return "Invalid payload", 400
        except stripe.error.SignatureVerificationError:
            return "Invalid signature", 400

        # 处理结算完成事件
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            order_no = session.get('metadata', {}).get('order_no')
            payment_intent = session.get('payment_intent')
            
            if order_no:
                # 状态机：幂等拦截，防止重复回调产生重复记账和重复订阅
                order = Order.query.filter_by(order_no=order_no).first()
                if order and order.status == "pending":
                    now = datetime.now(timezone.utc)
                    order.status = "paid"
                    order.paid_at = now
                    
                    # 生成正式支付流水
                    payment = PaymentRecord(
                        order_id=order.id, 
                        payment_method="stripe",
                        transaction_id=payment_intent,
                        amount=order.amount, 
                        currency=order.currency,
                        status="success",
                        raw_response=_json.dumps(session)
                    )
                    db.session.add(payment)
                    
                    # **重点**：支付成功流转后，才真正下发并激活订阅（防白嫖）
                    _activate_subscription(order.user_id, order, now)
                    
                    # 优惠码核销
                    if order.promo_code_id:
                        promo = PromoCode.query.get(order.promo_code_id)
                        if promo:
                            promo.used_count += 1
                            usage = PromoUsage(promo_code_id=promo.id, user_id=order.user_id, order_id=order.id)
                            db.session.add(usage)
                            
                    db.session.commit()
                    track_payment(order.user_id, float(order.amount), order.plan.name if order.plan else "")

        return success(message="webhook completed")

    @bp.route("/order/<order_no>", methods=["GET"])
    @jwt_required_custom()
    def get_order(order_no, **kwargs):
        current_user = kwargs["current_user"]
        order = Order.query.filter_by(order_no=order_no, user_id=current_user.id).first()
        if not order:
            return error("订单不存在", 404)
        payments = [p.to_dict() for p in order.payments.all()]
        return success({"order": order.to_dict(), "payments": payments})

    @bp.route("/simulate-pay", methods=["POST"])
    @jwt_required_custom()
    def simulate_payment(**kwargs):
        current_user = kwargs["current_user"]
        # 安全拦截：生产环境拒绝模拟支付
        import os
        if os.getenv("FLASK_ENV") == "production":
            return error("生产安全拦截：此环境禁止使用 simulate-pay 兜底支付")
            
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
        
        _activate_subscription(current_user.id, order, now)
        db.session.commit()
        
        from backend.models.user import User
        user = User.query.get(current_user.id)
        sub = user.get_active_subscription()
        return success({"order": order.to_dict(),
                        "subscription": sub.to_dict() if sub else None}, "测试环境直接模拟支付成功")

    return bp

def _activate_subscription(user_id, order, now):
    period_end = now + timedelta(days=365 if order.billing_cycle == "yearly" else 30)
    sub = Subscription.query.filter_by(user_id=user_id, status="active").first()
    if sub:
        sub.plan_id = order.plan_id
        sub.billing_cycle = order.billing_cycle
        sub.current_period_start = now
        sub.current_period_end = period_end
        sub.updated_at = now
    else:
        sub = Subscription(user_id=user_id, plan_id=order.plan_id,
                           billing_cycle=order.billing_cycle, status="active",
                           current_period_start=now, current_period_end=period_end)
        db.session.add(sub)
    order.subscription_id = sub.id

def _get_available_methods():
    methods = []
    if config.STRIPE_SECRET_KEY:
        methods.append({"id": "stripe", "name": "Stripe", "enabled": True})
    methods.append({"id": "manual", "name": "人工处理", "enabled": True})
    return methods
