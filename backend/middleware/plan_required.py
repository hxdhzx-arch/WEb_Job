"""
plan_required.py — 套餐权限检查装饰器
"""
from functools import wraps
from backend.utils.response import error


def plan_required(min_plan: str):
    """
    检查用户套餐是否满足最低要求
    min_plan: "free" / "pro" / "enterprise"
    """
    plan_levels = {"free": 0, "pro": 1, "enterprise": 2}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                return error("请先登录", 401)

            user_plan = current_user.get_current_plan()
            if not user_plan:
                return error("请先选择套餐", 403)

            user_level = plan_levels.get(user_plan.name, 0)
            required_level = plan_levels.get(min_plan, 0)

            if user_level < required_level:
                return error(
                    f"该功能需要 {min_plan} 或更高套餐，当前套餐: {user_plan.display_name}",
                    403
                )

            kwargs["current_plan"] = user_plan
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def feature_required(feature_name: str):
    """检查用户的套餐是否包含指定功能"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                return error("请先登录", 401)

            user_plan = current_user.get_current_plan()
            if not user_plan:
                return error("请先选择套餐", 403)

            if not user_plan.has_feature(feature_name):
                return error(
                    f"当前套餐不包含该功能，请升级到更高级套餐",
                    403
                )

            kwargs["current_plan"] = user_plan
            return fn(*args, **kwargs)
        return wrapper
    return decorator
