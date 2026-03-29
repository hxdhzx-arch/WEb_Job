"""
usage_guard.py — 用量额度检查装饰器
"""
from functools import wraps
from flask import request
from backend.models.usage import get_daily_usage, get_monthly_usage, record_usage
from backend.utils.response import error


def usage_guard(feature_name: str):
    """
    检查用户日/月额度并自动记录用量
    需要配合 @jwt_required_custom() 使用，会从 kwargs 获取 current_user
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                return error("请先登录", 401)

            plan = current_user.get_current_plan()

            if plan:
                # 检查每日额度
                daily_limit = plan.max_ai_calls_daily
                if daily_limit > 0:  # -1 = 无限
                    daily_used = get_daily_usage(current_user.id, feature_name)
                    if daily_used >= daily_limit:
                        return error(
                            f"今日 {feature_name} 调用次数已达上限 ({daily_limit} 次)，明天再试或升级套餐",
                            429
                        )

                # 检查每月额度
                monthly_limit = plan.max_ai_calls_monthly
                if monthly_limit > 0:
                    monthly_used = get_monthly_usage(current_user.id, feature_name)
                    if monthly_used >= monthly_limit:
                        return error(
                            f"本月 {feature_name} 调用次数已达上限 ({monthly_limit} 次)，请升级套餐",
                            429
                        )

            # 注入 feature_name 和 record 函数
            kwargs["feature_name"] = feature_name
            kwargs["record_usage_fn"] = lambda status="success", err=None: record_usage(
                user_id=current_user.id,
                feature=feature_name,
                ip=request.remote_addr,
                status=status,
                error_msg=err,
            )

            return fn(*args, **kwargs)
        return wrapper
    return decorator
