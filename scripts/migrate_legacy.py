"""
scripts/migrate_legacy.py — 迁移旧数据库数据
将 services/database.py 的 SQLite 数据迁移到新 SQLAlchemy 模型

运行: python scripts/migrate_legacy.py
"""
import sys
import os
import sqlite3
import json
import uuid as _uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

LEGACY_DB = os.path.join(os.path.dirname(__file__), "..", "data", "resume_ai.db")


def migrate():
    if not os.path.exists(LEGACY_DB):
        print("[提示] 旧数据库不存在，跳过迁移")
        return

    from app import create_app
    from backend.extensions import db
    from backend.models.user import User
    from backend.models.resume import Resume
    from backend.models.review import Review

    app = create_app()

    # 读取旧数据
    old_conn = sqlite3.connect(LEGACY_DB)
    old_conn.row_factory = sqlite3.Row

    with app.app_context():
        db.create_all()

        # 迁移用户
        old_users = old_conn.execute("SELECT * FROM users").fetchall()
        user_id_map = {}  # old user_id -> new User.id

        migrated_users = 0
        for ou in old_users:
            old_uid = ou["user_id"]

            # 检查是否已迁移
            existing = User.query.filter_by(uuid=old_uid).first()
            if existing:
                user_id_map[old_uid] = existing.id
                continue

            user = User(
                uuid=old_uid,
                email=ou["bind_email"] if ou["bind_email"] else None,
                phone=ou["bind_phone"] if ou["bind_phone"] else None,
                nickname="用户",
                role="user",
                credits_left=ou["credits_left"] or 0,
                total_used=ou["total_used"] or 0,
                device_hash=ou["device_hash"] or "",
                ip_address=ou["ip_address"] or "",
                login_count=ou["login_count"] or 0,
                created_at=datetime.fromtimestamp(ou["created_at"], tz=timezone.utc)
                    if ou["created_at"] else datetime.now(timezone.utc),
                updated_at=datetime.fromtimestamp(ou["updated_at"], tz=timezone.utc)
                    if ou["updated_at"] else datetime.now(timezone.utc),
            )
            if ou["last_login_at"]:
                user.last_login_at = datetime.fromtimestamp(ou["last_login_at"], tz=timezone.utc)

            db.session.add(user)
            db.session.flush()  # 获取 user.id
            user_id_map[old_uid] = user.id
            migrated_users += 1

        db.session.commit()
        print(f"[✓] 迁移用户: {migrated_users} 条 (跳过已存在: {len(old_users) - migrated_users})")

        # 迁移简历
        try:
            old_resumes = old_conn.execute("SELECT * FROM resumes").fetchall()
            migrated_resumes = 0
            for r in old_resumes:
                old_uid = r["user_id"]
                new_uid = user_id_map.get(old_uid)
                if not new_uid:
                    continue

                # 检查是否已存在
                exists = Resume.query.filter_by(
                    user_id=new_uid, title=r["title"]
                ).first()
                if exists:
                    continue

                try:
                    resume_data = json.loads(r["resume_data"]) if r["resume_data"] else {}
                except (json.JSONDecodeError, TypeError):
                    resume_data = {}

                try:
                    template_config = json.loads(r["template_config"]) if r["template_config"] else {}
                except (json.JSONDecodeError, TypeError):
                    template_config = {}

                resume = Resume(
                    user_id=new_uid,
                    title=r["title"] or "未命名简历",
                    resume_data=resume_data,
                    template_config=template_config,
                    is_default=bool(r["is_default"]),
                    created_at=datetime.fromtimestamp(r["created_at"], tz=timezone.utc)
                        if r["created_at"] else datetime.now(timezone.utc),
                    updated_at=datetime.fromtimestamp(r["updated_at"], tz=timezone.utc)
                        if r["updated_at"] else datetime.now(timezone.utc),
                )
                db.session.add(resume)
                migrated_resumes += 1

            db.session.commit()
            print(f"[✓] 迁移简历: {migrated_resumes} 条")
        except sqlite3.OperationalError:
            print("[提示] 旧数据库中无 resumes 表，跳过")

        # 迁移评价
        try:
            old_reviews = old_conn.execute("SELECT * FROM reviews").fetchall()
            migrated_reviews = 0
            for rv in old_reviews:
                old_uid = rv["user_id"]
                new_uid = user_id_map.get(old_uid)
                if not new_uid:
                    continue

                review = Review(
                    user_id=new_uid,
                    feature=rv["feature"] or "general",
                    rating=rv["rating"],
                    content=rv["content"] or "",
                    is_anonymous=bool(rv["is_anonymous"]),
                    display_name=rv["display_name"] or "匿名用户",
                    credits_awarded=rv["credits_awarded"] or 0,
                    created_at=datetime.fromtimestamp(rv["created_at"], tz=timezone.utc)
                        if rv["created_at"] else datetime.now(timezone.utc),
                )
                db.session.add(review)
                migrated_reviews += 1

            db.session.commit()
            print(f"[✓] 迁移评价: {migrated_reviews} 条")
        except sqlite3.OperationalError:
            print("[提示] 旧数据库中无 reviews 表，跳过")

    old_conn.close()
    print("\n[✓] 数据迁移完成！")


if __name__ == "__main__":
    migrate()
