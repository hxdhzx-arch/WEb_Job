"""
models/verify_code.py — 验证码模型
"""
from datetime import datetime, timezone
from backend.extensions import db


class VerifyCode(db.Model):
    __tablename__ = "saas_verify_codes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    target = db.Column(db.String(255), nullable=False, index=True,
                       comment="邮箱或手机号")
    code = db.Column(db.String(10), nullable=False)
    purpose = db.Column(db.String(30), nullable=False, default="bind",
                        comment="bind / login / register / reset_password / verify_email")
    attempts = db.Column(db.Integer, default=0)
    used = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
