#!/bin/bash
set -e

# ==========================================
# 简历生成器 Pro - 生产环境启动脚本 (Gunicorn)
# ==========================================

echo "[🚀] 正在启动简历服务生产环境..."

# 检查环境变量
if [ "$FLASK_ENV" != "production" ]; then
    echo "[警告] 当前 FLASK_ENV 不是 production，系统可能退回开发模式或拒绝启动。"
    echo "[!] 建议先执行: export FLASK_ENV=production"
fi

# 等待数秒数据库 Ready（针对刚拉起的 Postgres 服务）
echo "[WAIT] 检查数据库连通性..."
python3 -c "
import os, sys, time
from sqlalchemy import create_engine
url = os.getenv('DATABASE_URL')
if not url:
    print('【致命】未配置 DATABASE_URL')
    sys.exit(1)
if url.startswith('sqlite'):
    print('【致命】生产环境严禁使用 SQLite，请变更为 PostgreSQL 或 MySQL')
    sys.exit(1)
    
engine = create_engine(url, pool_pre_ping=True)
retries = 30
while retries > 0:
    try:
        conn = engine.connect()
        conn.close()
        print('【成功】数据库连通正常')
        sys.exit(0)
    except Exception as e:
        print(f'等待数据库响应中... (剩余 {retries} 次重试)')
        time.sleep(2)
        retries -= 1
print('【失败】数据库连接超时')
sys.exit(1)
" || exit 1


echo "[MIGRATE] 正在执行数据库迁移..."
# 针对生产，我们绝对不使用 db.create_all()，而是纯依赖升级迁移
export FLASK_APP=app.py
flask db upgrade

echo "[START] 启动 Gunicorn 多线程并发服务器..."
# 请确保 gunicorn.conf.py 的 workers / threads 调配符合你的物理机核心数
exec gunicorn -c gunicorn.conf.py app:app
