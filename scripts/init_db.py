"""
scripts/init_db.py — 初始化数据库 + 种子数据
运行: python scripts/init_db.py
"""
import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from backend.extensions import db
from backend.models import Plan, User
import config


def init_database():
    app = create_app()
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("[✓] 所有数据表已创建")

        # 插入种子数据：套餐
        _seed_plans()

        # 创建管理员
        _seed_admin()

        print("\n[✓] 数据库初始化完成！")


def _seed_plans():
    """创建默认套餐"""
    plans = [
        {
            "name": "free",
            "display_name": "免费版",
            "description": "基础功能，适合个人体验",
            "price_monthly": 0,
            "price_yearly": 0,
            "max_ai_calls_daily": 5,
            "max_ai_calls_monthly": 50,
            "max_resumes": 3,
            "features": {
                "resume_analyze": True,
                "jd_match": True,
                "auto_fill": False,
                "polish": False,
                "career_advisor": False,
                "keyword_inject": False,
                "export_word": True,
                "cloud_sync": False,
            },
            "sort_order": 0,
        },
        {
            "name": "pro",
            "display_name": "Pro 专业版",
            "description": "全功能解锁，适合求职者",
            "price_monthly": 29.9,
            "price_yearly": 199.0,
            "max_ai_calls_daily": 50,
            "max_ai_calls_monthly": 500,
            "max_resumes": 10,
            "features": {
                "resume_analyze": True,
                "jd_match": True,
                "auto_fill": True,
                "polish": True,
                "career_advisor": True,
                "keyword_inject": True,
                "export_word": True,
                "cloud_sync": True,
                "priority_support": False,
            },
            "sort_order": 1,
        },
        {
            "name": "enterprise",
            "display_name": "企业版",
            "description": "无限使用，团队协作，专属支持",
            "price_monthly": 99.0,
            "price_yearly": 799.0,
            "max_ai_calls_daily": -1,
            "max_ai_calls_monthly": -1,
            "max_resumes": 50,
            "features": {
                "resume_analyze": True,
                "jd_match": True,
                "auto_fill": True,
                "polish": True,
                "career_advisor": True,
                "keyword_inject": True,
                "export_word": True,
                "cloud_sync": True,
                "priority_support": True,
                "api_access": True,
                "custom_branding": True,
            },
            "sort_order": 2,
        },
    ]

    for p_data in plans:
        existing = Plan.query.filter_by(name=p_data["name"]).first()
        if existing:
            print(f"  [跳过] 套餐 '{p_data['name']}' 已存在")
            continue

        plan = Plan(**p_data)
        db.session.add(plan)
        print(f"  [+] 创建套餐: {p_data['display_name']}")

    db.session.commit()


def _seed_admin():
    """创建管理员账号"""
    import uuid
    admin_email = config.ADMIN_EMAIL
    admin_password = config.ADMIN_PASSWORD

    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        print(f"  [跳过] 管理员 '{admin_email}' 已存在")
        return

    admin = User(
        uuid=str(uuid.uuid4()),
        email=admin_email,
        nickname="管理员",
        role="admin",
        email_verified=True,
        credits_left=99999,
    )
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()
    print(f"  [+] 创建管理员: {admin_email}")


if __name__ == "__main__":
    init_database()
