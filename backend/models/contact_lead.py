"""
models/contact_lead.py — 联系表单 / 线索收集
"""
from datetime import datetime, timezone
from backend.extensions import db


class ContactLead(db.Model):
    __tablename__ = "saas_contact_leads"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(255), nullable=True, index=True)
    phone = db.Column(db.String(20), nullable=True)
    company = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=True)

    source = db.Column(db.String(50), default="contact_form",
                       comment="landing_page / contact_form / pricing_page / ...")
    status = db.Column(db.String(20), default="new",
                       comment="new / contacted / converted / archived")

    # 可关联已注册用户
    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=True)

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "message": self.message,
            "source": self.source,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
