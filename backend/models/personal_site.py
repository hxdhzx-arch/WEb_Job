"""
models/personal_site.py — AI 个人网站（独立于 Resume 的个人主页/作品集模型）
"""
import re
import uuid as _uuid
from datetime import datetime, timezone
from backend.extensions import db


class PersonalSite(db.Model):
    __tablename__ = "saas_personal_sites"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False, default="我的个人网站")
    prompt = db.Column(db.Text, nullable=True, comment="用户输入的生成提示词")

    # ── 核心数据 ──
    site_data = db.Column(db.JSON, nullable=False, default=dict, comment="结构化网站内容 JSON")
    site_config = db.Column(db.JSON, default=dict, comment="样式/模板/主题配置 JSON")

    # ── 上传资源（base64 或路径） ──
    avatar_data = db.Column(db.Text, nullable=True, comment="头像 base64")
    cover_data = db.Column(db.Text, nullable=True, comment="封面图 base64")

    # ── 发布 ──
    slug = db.Column(db.String(50), unique=True, nullable=True, index=True,
                     comment="公开短链 /site/<slug>")
    is_published = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # ── 时间戳 ──
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def generate_slug(self):
        """生成唯一 slug"""
        name = ""
        try:
            name = (self.site_data or {}).get("hero", {}).get("name", "")
        except (AttributeError, TypeError):
            pass
        if name:
            if re.search(r'[\u4e00-\u9fff]', name):
                base = "site-" + _uuid.uuid4().hex[:6]
            else:
                base = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')[:16]
        else:
            base = "site-" + _uuid.uuid4().hex[:6]

        slug = base
        counter = 1
        while PersonalSite.query.filter_by(slug=slug).first():
            slug = f"{base}-{counter}"
            counter += 1
        self.slug = slug
        return slug

    def to_dict(self, include_content=False):
        d = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "prompt": self.prompt,
            "slug": self.slug,
            "is_published": self.is_published,
            "view_count": self.view_count,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            d["site_data"] = self.site_data
            d["site_config"] = self.site_config
        return d

    def __repr__(self):
        return f"<PersonalSite {self.id} '{self.title}'>"
