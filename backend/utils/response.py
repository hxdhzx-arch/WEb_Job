"""
response.py — 统一 JSON 响应格式
"""
from flask import jsonify


def success(data=None, message="success", code=200):
    """成功响应"""
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), code


def error(message="请求失败", code=400, errors=None):
    """错误响应"""
    payload = {"success": False, "message": message}
    if errors:
        payload["errors"] = errors
    return jsonify(payload), code


def paginated(items, total, page, per_page, message="success"):
    """分页响应"""
    return jsonify({
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
        }
    }), 200
