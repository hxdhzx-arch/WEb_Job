"""
models/project_version.py — 项目文件版本控制（快照/回滚）
支持 Resume 与 Personal Site
"""
import uuid
from datetime import datetime, timezone
from backend.extensions import db

class ProjectVersion(db.Model):
    __tablename__ = "saas_project_versions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=False, index=True)
    
    project_type = db.Column(db.String(50), nullable=False, comment="项目类型 (resume / site)")
    project_id = db.Column(db.Integer, nullable=False, index=True, comment="原项目 ID")
    
    version_hash = db.Column(db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    version_note = db.Column(db.String(200), nullable=True, comment="版本提示 (如: 发布前自动存档)")
    
    # Snapshot data
    data_snapshot = db.Column(db.JSON, nullable=False, comment="内容 JSON 镜像")
    config_snapshot = db.Column(db.JSON, nullable=True, comment="配置 JSON 镜像")

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "project_type": self.project_type,
            "project_id": self.project_id,
            "version_hash": self.version_hash,
            "version_note": self.version_note,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<ProjectVersion {self.project_type}_{self.project_id} {self.version_hash}>"
