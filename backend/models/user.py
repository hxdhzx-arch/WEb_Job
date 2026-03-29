"""
models/user.py — 用户模型
"""
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from backend.extensions import db


class User(db.Model):
    __tablename__ = "saas_users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True,
                     comment="兼容旧前端 user_id")
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True,
                              comment="werkzeug 密码哈希; 验证码用户可无密码")
    nickname = db.Column(db.String(50), nullable=True, default="用户")
    avatar_url = db.Column(db.String(500), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="user",
                     comment="user / admin")
    email_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    # 兼容旧系统
    credits_left = db.Column(db.Integer, default=300, comment="兼容旧算力系统")
    total_used = db.Column(db.Integer, default=0)
    device_hash = db.Column(db.String(64), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)

    # 试用期
    trial_ends_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # 时间戳
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    login_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    subscriptions = db.relationship("Subscription", backref="user", lazy="dynamic")
    orders = db.relationship("Order", backref="user", lazy="dynamic")
    usage_logs = db.relationship("UsageLog", backref="user", lazy="dynamic")
    resumes = db.relationship("Resume", backref="user", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_trial_active(self) -> bool:
        if not self.trial_ends_at:
            return False
        return datetime.now(timezone.utc) < self.trial_ends_at

    def start_trial(self, days: int = 7):
        self.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=days)

    def get_active_subscription(self):
        """获取当前有效订阅"""
        from backend.models.subscription import Subscription
        return Subscription.query.filter_by(
            user_id=self.id, status="active"
        ).first()

    def get_current_plan(self):
        """获取当前套餐（优先有效订阅，否则免费版）"""
        from backend.models.plan import Plan
        sub = self.get_active_subscription()
        if sub:
            return sub.plan
        return Plan.query.filter_by(name="free").first()

    def to_dict(self, include_sensitive=False):
        d = {
            "id": self.id,
            "uuid": self.uuid,
            "email": self.email,
            "phone": self.phone,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "email_verified": self.email_verified,
            "is_active": self.is_active,
            "credits_left": self.credits_left,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "login_count": self.login_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_sensitive:
            d["device_hash"] = self.device_hash
            d["ip_address"] = self.ip_address
            d["total_used"] = self.total_used
        return d

    def __repr__(self):
        return f"<User {self.id} {self.email or self.uuid}>"
