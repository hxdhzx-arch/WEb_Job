"""
models/review.py — 评价模型
"""
from datetime import datetime, timezone
from backend.extensions import db


class Review(db.Model):
    __tablename__ = "saas_reviews"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=False, index=True)

    feature = db.Column(db.String(50), nullable=False, default="general")
    rating = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, default="")
    is_anonymous = db.Column(db.Boolean, default=False)
    display_name = db.Column(db.String(50), default="匿名用户")
    credits_awarded = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "feature": self.feature,
            "rating": self.rating,
            "content": self.content,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
