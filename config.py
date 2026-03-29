"""
config.py — 全局配置与 API Key 轮询管理
支持 SQLite / MySQL / PostgreSQL 切换
"""

import os
import threading
from datetime import timedelta
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ──────────────────────────────────────
# 基础配置
# ──────────────────────────────────────

PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 10))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ──────────────────────────────────────
# 数据库配置
# ──────────────────────────────────────

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DB = "sqlite:///" + os.path.join(_BASE_DIR, "data", "resume_ai.db")
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

# SQLAlchemy 配置字典（create_app 使用）
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
}

# ──────────────────────────────────────
# JWT 配置
# ──────────────────────────────────────

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(
    seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 86400))
)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(
    seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))
)

# ──────────────────────────────────────
# SMTP 邮件配置（验证码发送）
# ──────────────────────────────────────

SMTP_HOST = os.getenv("SMTP_HOST", "")           # smtp.qq.com / smtp.gmail.com
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))      # 465=SSL / 587=STARTTLS
SMTP_USER = os.getenv("SMTP_USER", "")            # 发件邮箱
SMTP_PASS = os.getenv("SMTP_PASS", "")            # 授权码（非邮箱密码）
SMTP_FROM = os.getenv("SMTP_FROM", "")            # 发件人显示名

if not SMTP_HOST:
    print("[提示] SMTP 未配置，验证码将打印到控制台（开发模式）")

# ──────────────────────────────────────
# 支付配置（预留）
# ──────────────────────────────────────

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "")
ALIPAY_PRIVATE_KEY = os.getenv("ALIPAY_PRIVATE_KEY", "")
ALIPAY_PUBLIC_KEY = os.getenv("ALIPAY_PUBLIC_KEY", "")
ALIPAY_NOTIFY_URL = os.getenv("ALIPAY_NOTIFY_URL", "")

WECHAT_PAY_APP_ID = os.getenv("WECHAT_PAY_APP_ID", "")
WECHAT_PAY_MCH_ID = os.getenv("WECHAT_PAY_MCH_ID", "")
WECHAT_PAY_API_KEY = os.getenv("WECHAT_PAY_API_KEY", "")
WECHAT_PAY_NOTIFY_URL = os.getenv("WECHAT_PAY_NOTIFY_URL", "")

# ──────────────────────────────────────
# 管理员配置
# ──────────────────────────────────────

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123456")

# ──────────────────────────────────────
# 试用期
# ──────────────────────────────────────

TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", 7))

# ──────────────────────────────────────
# API Key 轮询池
# ──────────────────────────────────────

class KeyPool:
    """
    Gemini API Key 轮询池
    - 线程安全的 Round-Robin 轮询
    - 支持标记失败 Key 并自动跳过
    - 所有 Key 失败时自动重置
    """

    def __init__(self, keys: list):
        if not keys:
            raise ValueError(
                "请在 .env 文件中配置真实的 GEMINI_API_KEYS，多个 Key 用逗号分隔"
            )
        self._keys = keys
        self._index = 0
        self._failed = set()
        self._lock = threading.Lock()

    @property
    def total(self) -> int:
        return len(self._keys)

    @property
    def available(self) -> int:
        return self.total - len(self._failed)

    def next_key(self) -> str:
        with self._lock:
            if len(self._failed) >= self.total:
                self._failed.clear()

            for _ in range(self.total):
                idx = self._index % self.total
                self._index += 1
                if idx not in self._failed:
                    return self._keys[idx]

            self._failed.clear()
            self._index = 1
            return self._keys[0]

    def mark_failed(self, key: str):
        with self._lock:
            try:
                idx = self._keys.index(key)
                self._failed.add(idx)
            except ValueError:
                pass

    def reset_all(self):
        with self._lock:
            self._failed.clear()
            self._index = 0


# 解析 API Keys 并初始化 Key 池
_raw_keys = os.getenv("GEMINI_API_KEYS", "")
API_KEYS = [k.strip() for k in _raw_keys.split(",") if k.strip()]

if not API_KEYS:
    print("[错误] 未配置 GEMINI_API_KEYS，请检查 .env 文件")
    print("[提示] 格式: GEMINI_API_KEYS=key1,key2,key3")
    import sys
    sys.exit(1)

key_pool = KeyPool(API_KEYS)
print("[ok] 已加载 %d 个 API Key" % key_pool.total)
