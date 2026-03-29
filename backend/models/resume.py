"""
models/resume.py — 云端简历 (含网页发布功能)
"""
import re
import uuid as _uuid
from datetime import datetime, timezone
from backend.extensions import db


class Resume(db.Model):
    __tablename__ = "saas_resumes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=False, index=True)

    title = db.Column(db.String(100), nullable=False, default="未命名简历")
    resume_data = db.Column(db.JSON, nullable=False, comment="简历内容 JSON")
    template_config = db.Column(db.JSON, default=dict, comment="编辑器模板配置 JSON")
    is_default = db.Column(db.Boolean, default=False)

    # ── 网页简历发布 ──
    slug = db.Column(db.String(50), unique=True, nullable=True, index=True,
                     comment="网页简历短链标识 /r/<slug>")
    is_published = db.Column(db.Boolean, default=False, comment="是否已发布为网页")
    web_config = db.Column(db.JSON, default=dict, comment="网页简历配置 JSON")
    password_hash = db.Column(db.String(255), nullable=True, comment="网页访问密码哈希")
    view_count = db.Column(db.Integer, default=0, comment="网页浏览次数")
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # ── 时间戳 ──
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── slug 生成 ──
    def generate_slug(self):
        """根据简历内容自动生成 slug"""
        name = ""
        try:
            name = (self.resume_data or {}).get("basic", {}).get("name", "")
        except (AttributeError, TypeError):
            pass
        if name:
            # 简单拼音转换：中文名用 UUID 短码，英文名用小写
            if re.search(r'[\u4e00-\u9fff]', name):
                base = _uuid.uuid4().hex[:8]
            else:
                base = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')[:20]
        else:
            base = _uuid.uuid4().hex[:8]
        # 检查唯一性
        slug = base
        counter = 1
        while Resume.query.filter_by(slug=slug).first():
            slug = f"{base}-{counter}"
            counter += 1
        self.slug = slug
        return slug

    def set_password(self, password):
        """设置网页访问密码"""
        if not password:
            self.password_hash = None
            return
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        """验证网页访问密码"""
        if not self.password_hash:
            return True
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_content=False):
        d = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "is_default": self.is_default,
            "is_published": self.is_published,
            "slug": self.slug,
            "view_count": self.view_count,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            d["resume_data"] = self.resume_data
            d["template_config"] = self.template_config
            d["web_config"] = self.web_config
        # 预览：提取姓名
        try:
            d["preview_name"] = (self.resume_data or {}).get("basic", {}).get("name", "")
        except (AttributeError, TypeError):
            d["preview_name"] = ""
        return d

    def __repr__(self):
        return f"<Resume {self.id} '{self.title}'>"
