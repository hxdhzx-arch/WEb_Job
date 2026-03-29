"""
models/plan.py — 套餐模型
"""
from backend.extensions import db


class Plan(db.Model):
    __tablename__ = "saas_plans"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), unique=True, nullable=False,
                     comment="free / pro / enterprise")
    display_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # 价格
    price_monthly = db.Column(db.Numeric(10, 2), default=0,
                              comment="月付价格 (元/美元)")
    price_yearly = db.Column(db.Numeric(10, 2), default=0,
                             comment="年付价格 (元/美元)")
    currency = db.Column(db.String(10), default="CNY",
                         comment="CNY / USD")

    # 额度限制
    max_ai_calls_daily = db.Column(db.Integer, default=5,
                                   comment="每日 AI 调用上限, -1=无限")
    max_ai_calls_monthly = db.Column(db.Integer, default=100,
                                     comment="每月 AI 调用上限, -1=无限")
    max_resumes = db.Column(db.Integer, default=3,
                            comment="最大简历数")

    # 功能开关 (存为 JSON 字符串)
    features = db.Column(db.JSON, default=dict,
                         comment='{"resume_analyze": true, "jd_match": true, ...}')

    # 排序 & 状态
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    # 关系
    subscriptions = db.relationship("Subscription", backref="plan", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "price_monthly": float(self.price_monthly or 0),
            "price_yearly": float(self.price_yearly or 0),
            "currency": self.currency,
            "max_ai_calls_daily": self.max_ai_calls_daily,
            "max_ai_calls_monthly": self.max_ai_calls_monthly,
            "max_resumes": self.max_resumes,
            "features": self.features or {},
            "sort_order": self.sort_order,
        }

    def has_feature(self, feature_name: str) -> bool:
        """检查套餐是否包含某功能"""
        if not self.features:
            return False
        return self.features.get(feature_name, False)

    def __repr__(self):
        return f"<Plan {self.name}>"
