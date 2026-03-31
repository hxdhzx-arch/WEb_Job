"""
models/user_session.py — 预留的用户设备与会话态概览
"""
from datetime import datetime, timezone
from backend.extensions import db

class UserSession(db.Model):
    __tablename__ = "saas_user_sessions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('saas_users.id'), nullable=False, index=True)
    refresh_jti = db.Column(db.String(36), nullable=False, index=True, unique=True)
    
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    device_name = db.Column(db.String(128), nullable=True, comment="未来可解析UA填充")
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_active_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def record_session(cls, user_id, refresh_jti, ip, ua):
        from backend.extensions import db
        s = cls(user_id=user_id, refresh_jti=refresh_jti, ip_address=ip, user_agent=ua)
        db.session.add(s)

    def to_dict(self):
        return {
            "id": self.id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_name": self.device_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
        }
