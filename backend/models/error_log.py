"""
models/error_log.py — 错误日志
"""
from datetime import datetime, timezone
from backend.extensions import db


class ErrorLog(db.Model):
    __tablename__ = "saas_error_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    level = db.Column(db.String(20), nullable=False, default="error",
                      comment="error / warning / info")
    module = db.Column(db.String(100), nullable=True, comment="出错模块")
    endpoint = db.Column(db.String(200), nullable=True, comment="请求路径")
    method = db.Column(db.String(10), nullable=True)
    message = db.Column(db.Text, nullable=False)
    traceback = db.Column(db.Text, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "level": self.level,
            "module": self.module,
            "endpoint": self.endpoint,
            "method": self.method,
            "message": self.message,
            "traceback": self.traceback,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def log_error(message: str, module: str = None, traceback_str: str = None,
              user_id: int = None, ip: str = None, endpoint: str = None,
              method: str = None, level: str = "error"):
    """快捷记录错误日志"""
    entry = ErrorLog(
        level=level,
        module=module,
        endpoint=endpoint,
        method=method,
        message=message[:2000],
        traceback=traceback_str[:5000] if traceback_str else None,
        user_id=user_id,
        ip_address=ip,
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(entry)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
