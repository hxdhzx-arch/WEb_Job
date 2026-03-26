"""
privacy_mask.py — PII 脱敏引擎
在发送给大模型之前，自动擦除手机号、邮箱、身份证等隐私信息
"""
import re

# Phone: 13x-19x, with optional separators
_PHONE = re.compile(r'(?<!\d)(1[3-9]\d[\s\-]?\d{4}[\s\-]?\d{4})(?!\d)')
# Email
_EMAIL = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
# ID card: 18 digits or 17+X
_IDCARD = re.compile(r'(?<!\d)\d{17}[\dXx](?!\d)')
# QQ number (5-11 digits standalone)
_QQ = re.compile(r'(?:QQ|qq|Qq)[\s:：]?\d{5,11}')
# WeChat pattern
_WECHAT = re.compile(r'(?:微信|WeChat|wechat)[\s:：]?\S{6,20}')

_PATTERNS = [
    (_PHONE, '[手机已隐藏]'),
    (_EMAIL, '[邮箱已隐藏]'),
    (_IDCARD, '[证件号已隐藏]'),
    (_QQ, '[QQ已隐藏]'),
    (_WECHAT, '[微信已隐藏]'),
]

def mask_pii(text: str) -> str:
    """将文本中的 PII 信息替换为占位符"""
    if not text:
        return text
    masked = text
    for pattern, placeholder in _PATTERNS:
        masked = pattern.sub(placeholder, masked)
    return masked

def mask_resume_for_ai(text: str) -> str:
    """专门用于发送给 AI 的脱敏版本，保留结构但隐藏身份"""
    return mask_pii(text)
