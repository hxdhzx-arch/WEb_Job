"""
extensions.py — Flask 扩展实例
在 create_app 中调用 init_app 初始化
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_migrate import Migrate

# SQLAlchemy ORM
db = SQLAlchemy()

# JWT 鉴权
jwt = JWTManager()

# 接口限流
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# CORS
cors = CORS()

# 数据库迁移
migrate = Migrate()
