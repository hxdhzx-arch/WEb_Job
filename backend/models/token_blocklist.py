"""
models/token_blocklist.py — JWT Token 黑名单与作废管理
"""
from datetime import datetime, timezone
from backend.extensions import db

class TokenBlocklist(db.Model):
    __tablename__ = "saas_token_blocklist"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    token_type = db.Column(db.String(10), nullable=False, comment="access / refresh")
    user_id = db.Column(db.Integer, db.ForeignKey('saas_users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    @classmethod
    def revoke_token(cls, jti: str, token_type: str, user_id: int):
        from backend.extensions import db
        blocklist = cls(jti=jti, token_type=token_type, user_id=user_id)
        db.session.add(blocklist)
