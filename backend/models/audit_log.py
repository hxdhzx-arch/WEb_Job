"""
models/audit_log.py — 管理后台操作审计日志
"""
from datetime import datetime, timezone
from backend.extensions import db

class AuditLog(db.Model):
    __tablename__ = "saas_audit_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('saas_users.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False, comment="核心危险操作：修改额度/调整套餐/删除用户/系统导出...")
    target_id = db.Column(db.String(50), nullable=True, comment="被操作的对象ID或流水号")
    details = db.Column(db.JSON, nullable=True, comment="具体操作前后数据Diff")
    ip_address = db.Column(db.String(45), nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    @classmethod
    def log(cls, admin_id, action, target_id=None, details=None, ip=None):
        from backend.extensions import db
        record = cls(admin_id=admin_id, action=action, target_id=str(target_id) if target_id else None, details=details or {}, ip_address=ip)
        db.session.add(record)
        try:
            db.session.commit()
        except:
            db.session.rollback()
