"""
scripts/create_admin.py — 创建管理员账号
运行: python scripts/create_admin.py [email] [password]
"""
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from backend.extensions import db
from backend.models.user import User


def create_admin(email=None, password=None):
    app = create_app()
    with app.app_context():
        if not email:
            email = input("管理员邮箱: ").strip()
        if not password:
            password = input("管理员密码: ").strip()

        if not email or not password:
            print("[错误] 邮箱和密码不能为空")
            return

        existing = User.query.filter_by(email=email).first()
        if existing:
            # 升级为管理员
            existing.role = "admin"
            existing.set_password(password)
            db.session.commit()
            print(f"[✓] 已将 {email} 升级为管理员")
            return

        admin = User(
            uuid=str(uuid.uuid4()),
            email=email,
            nickname="管理员",
            role="admin",
            email_verified=True,
            credits_left=99999,
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"[✓] 管理员创建成功: {email}")


if __name__ == "__main__":
    args = sys.argv[1:]
    email = args[0] if len(args) > 0 else None
    password = args[1] if len(args) > 1 else None
    create_admin(email, password)
