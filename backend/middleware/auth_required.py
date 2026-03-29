"""
auth_required.py — JWT 鉴权装饰器
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from backend.models.user import User
from backend.utils.response import error


def jwt_required_custom():
    """自定义 JWT 鉴权装饰器，注入 current_user"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return error("请先登录", 401)

            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))
            if not user:
                return error("用户不存在", 401)
            if not user.is_active:
                return error("账号已被禁用", 403)

            kwargs["current_user"] = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required():
    """管理员权限装饰器"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return error("请先登录", 401)

            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))
            if not user:
                return error("用户不存在", 401)
            if not user.is_active:
                return error("账号已被禁用", 403)
            if not user.is_admin:
                return error("权限不足", 403)

            kwargs["current_user"] = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator
