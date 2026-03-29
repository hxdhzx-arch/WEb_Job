"""
models/usage.py — 用量计费
"""
from datetime import datetime, timezone, date as _date
from backend.extensions import db


class UsageLog(db.Model):
    """单次 API 调用日志"""
    __tablename__ = "saas_usage_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=False, index=True)

    feature = db.Column(db.String(50), nullable=False, index=True,
                        comment="resume_analyze / jd_match / auto_fill / polish / career_advisor / ...")
    cost = db.Column(db.Integer, default=1, comment="本次消耗计数/算力")
    ip_address = db.Column(db.String(45), nullable=True)
    request_summary = db.Column(db.String(500), nullable=True,
                                comment="请求摘要 (脱敏后)")
    response_status = db.Column(db.String(20), default="success",
                                comment="success / error")
    error_message = db.Column(db.String(500), nullable=True)

    # 按量计费预留字段
    tokens_input = db.Column(db.Integer, default=0, comment="输入 Token 数")
    tokens_output = db.Column(db.Integer, default=0, comment="输出 Token 数")
    duration_ms = db.Column(db.Integer, default=0, comment="处理耗时 (毫秒)")

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "feature": self.feature,
            "cost": self.cost,
            "response_status": self.response_status,
            "error_message": self.error_message,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UsageSummary(db.Model):
    """每日用量汇总（定时任务生成）"""
    __tablename__ = "saas_usage_summaries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("saas_users.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    feature = db.Column(db.String(50), nullable=False)

    call_count = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Integer, default=0)
    total_tokens_input = db.Column(db.Integer, default=0)
    total_tokens_output = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.UniqueConstraint("user_id", "date", "feature", name="uq_usage_summary"),
    )

    def to_dict(self):
        return {
            "date": self.date.isoformat() if self.date else None,
            "feature": self.feature,
            "call_count": self.call_count,
            "total_cost": self.total_cost,
        }


def get_daily_usage(user_id: int, feature: str = None) -> int:
    """获取用户今日已使用次数"""
    today = _date.today()
    query = UsageLog.query.filter(
        UsageLog.user_id == user_id,
        db.func.date(UsageLog.created_at) == today,
        UsageLog.response_status == "success",
    )
    if feature:
        query = query.filter(UsageLog.feature == feature)
    return query.count()


def get_monthly_usage(user_id: int, feature: str = None) -> int:
    """获取用户本月已使用次数"""
    today = _date.today()
    first_day = today.replace(day=1)
    query = UsageLog.query.filter(
        UsageLog.user_id == user_id,
        db.func.date(UsageLog.created_at) >= first_day,
        UsageLog.response_status == "success",
    )
    if feature:
        query = query.filter(UsageLog.feature == feature)
    return query.count()


def record_usage(user_id: int, feature: str, ip: str = None,
                 cost: int = 1, status: str = "success",
                 error_msg: str = None, summary: str = None) -> UsageLog:
    """记录一次 API 调用"""
    log = UsageLog(
        user_id=user_id,
        feature=feature,
        cost=cost,
        ip_address=ip,
        request_summary=summary[:500] if summary else None,
        response_status=status,
        error_message=error_msg,
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(log)
    db.session.commit()
    return log
