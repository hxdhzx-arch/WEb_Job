"""
config.py — 全局配置与 API Key 轮询管理
支持环境隔离：DevelopmentConfig / ProductionConfig / TestingConfig
"""

import os
import sys
import threading
from datetime import timedelta
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = False
    TESTING = False
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 10))
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
    
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _DEFAULT_DB = "sqlite:///" + os.path.join(_BASE_DIR, "data", "resume_ai.db")
    DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 86400)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000)))
    
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "")
    
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
    
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123456")
    TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", 7))

class DevelopmentConfig(Config):
    DEBUG = True
    def __init__(self):
        if not self.SMTP_HOST:
            print("[提示] 开发模式：SMTP 未配置，验证码将打印到控制台")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

class ProductionConfig(Config):
    DEBUG = False
    def __init__(self):
        # 强制检查生产环境关键变量
        if not os.getenv("JWT_SECRET_KEY") or self.JWT_SECRET_KEY == "dev-secret-change-me":
            raise ValueError("[安全错误] 生产环境必须强制配置高强度的 JWT_SECRET_KEY")
        if self.ADMIN_PASSWORD == "admin123456":
            raise ValueError("[安全错误] 生产环境必须修改 ADMIN_PASSWORD 默认弱口令")
        if not self.SMTP_HOST:
            raise ValueError("[配置错误] 生产环境必须配置 SMTP 服务，防止应用无法发送验证码而阻断用户功能")
        if self.ALLOWED_ORIGINS == "*":
            raise ValueError("[安全错误] 生产环境必须通过 ALLOWED_ORIGINS 配置前端域名限制跨域，禁止使用 *")
        if self.SQLALCHEMY_DATABASE_URI.startswith("sqlite") or self.SQLALCHEMY_DATABASE_URI.startswith("sqlite+pysqlite"):
            raise ValueError("[灾难级配置错误] 生产环境数据库不可为单文件 SQLite（锁争用、低并发、易损坏）。请指定 PostgreSQL/MySQL 形式的 DATABASE_URL")
            
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": int(os.getenv("DB_POOL_SIZE", 20)),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", 1800)),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", 30)),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 40)),
            "pool_pre_ping": True,
        }

config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}

# 实例化当前配置，注入到全局供旧代码以 cfg.XXX 方式兼容调用
ACTIVE_ENV = os.getenv("FLASK_ENV", "development")
current_config = config.get(ACTIVE_ENV, config["default"])()

for key in dir(current_config):
    if key.isupper():
        globals()[key] = getattr(current_config, key)

class KeyPool:
    def __init__(self, keys: list):
        if not keys:
            raise ValueError("请在 .env 文件中配置真实的 GEMINI_API_KEYS，多个 Key 用逗号分隔")
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

_raw_keys = os.getenv("GEMINI_API_KEYS", "")
API_KEYS = [k.strip() for k in _raw_keys.split(",") if k.strip()]

if not API_KEYS:
    print("[错误] 未配置 GEMINI_API_KEYS，请检查 .env 文件")
    print("[提示] 格式: GEMINI_API_KEYS=key1,key2,key3")
    sys.exit(1)

key_pool = KeyPool(API_KEYS)
if ACTIVE_ENV == "development":
    print(f"[ok] 已加载 {key_pool.total} 个 API Key (当前环境: {ACTIVE_ENV})")
