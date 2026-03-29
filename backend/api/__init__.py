"""
backend/api/__init__.py — API Blueprint 注册
使用函数内创建蓝图，避免重复注册问题
"""
from flask import Blueprint


def register_blueprints(app):
    """注册所有 API Blueprint 到 Flask app"""
    from backend.api import auth, user, plan, subscription, payment, usage, promo, contact, admin
    from backend.api.web_resume import create_web_resume_bp

    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    # 每个模块提供 create_blueprint() 工厂函数
    api_v1.register_blueprint(auth.create_blueprint())
    api_v1.register_blueprint(user.create_blueprint())
    api_v1.register_blueprint(plan.create_blueprint())
    api_v1.register_blueprint(subscription.create_blueprint())
    api_v1.register_blueprint(payment.create_blueprint())
    api_v1.register_blueprint(usage.create_blueprint())
    api_v1.register_blueprint(promo.create_blueprint())
    api_v1.register_blueprint(contact.create_blueprint())
    api_v1.register_blueprint(admin.create_blueprint())
    api_v1.register_blueprint(create_web_resume_bp())

    app.register_blueprint(api_v1)
