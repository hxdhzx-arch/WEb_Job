#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=================================="
echo "  AI 简历 SaaS 平台 - 启动中..."
echo "=================================="

export PYTHONIOENCODING=utf-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 python3"
    exit 1
fi

echo "[✓] Python 版本: $(python3 --version)"

echo "[信息] 安装依赖..."
pip3 install -r requirements.txt --quiet --break-system-packages 2>/dev/null \
    || pip3 install -r requirements.txt --quiet

echo "[✓] 依赖安装完成"
echo "[✓] 环境变量已加载"

# 确保 data 目录存在
mkdir -p data

# 初始化数据库（首次运行时）
if [ ! -f "data/.db_initialized" ]; then
    echo "[信息] 首次运行，初始化数据库..."
    python3 scripts/init_db.py
    touch data/.db_initialized
    echo "[✓] 数据库初始化完成"
fi

_DEFAULT_PORT=5000
_PORT_LINE="$(grep -E '^[[:space:]]*PORT=' .env 2>/dev/null | head -1 || true)"
_DISPLAY_PORT="$(echo "$_PORT_LINE" | cut -d'=' -f2- | tr -d ' \r')"
[ -z "$_DISPLAY_PORT" ] && _DISPLAY_PORT="$_DEFAULT_PORT"

echo "=================================="
echo "  服务启动于: http://localhost:${_DISPLAY_PORT}"
echo "  API 文档:   http://localhost:${_DISPLAY_PORT}/api/v1/"
echo "  按 Ctrl+C 停止服务"
echo "=================================="

python3 app.py
