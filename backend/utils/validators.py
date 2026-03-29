"""
validators.py — 参数校验工具
"""
import re

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
_PHONE_RE = re.compile(r'^1[3-9]\d{9}$')


def validate_email(email: str) -> bool:
    return bool(email and _EMAIL_RE.match(email.strip()))


def validate_phone(phone: str) -> bool:
    cleaned = re.sub(r'[\s\-]', '', phone.strip()) if phone else ''
    return bool(_PHONE_RE.match(cleaned))


def validate_password(password: str) -> tuple:
    """
    校验密码强度
    返回 (valid, error_msg)
    """
    if not password:
        return False, "密码不能为空"
    if len(password) < 6:
        return False, "密码至少 6 位"
    if len(password) > 128:
        return False, "密码过长"
    return True, None


def validate_nickname(nickname: str) -> tuple:
    if not nickname or not nickname.strip():
        return False, "昵称不能为空"
    if len(nickname.strip()) > 50:
        return False, "昵称不能超过 50 个字符"
    return True, None


def sanitize_string(s: str, max_len: int = 500) -> str:
    """清理字符串：去除首尾空白、截断"""
    if not s:
        return ""
    return s.strip()[:max_len]
