#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=================================="
echo "  AI 简历诊断系统 - 启动中..."
echo "=================================="

export PYTHONIOENCODING=utf-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 python3"
    exit 1
fi

echo "[✓] Python 版本: $(python3 --version)"

if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << REQEOF
flask==3.1.0
python-dotenv==1.1.0
PyMuPDF==1.25.3
REQEOF
fi

echo "[信息] 安装依赖..."
pip3 install -r requirements.txt --quiet --break-system-packages 2>/dev/null \
    || pip3 install -r requirements.txt --quiet

echo "[✓] 环境变量已加载"

echo "=================================="
echo "  服务启动于: http://localhost:$(grep PORT .env | head -1 | cut -d'=' -f2 | tr -d ' ')"
echo "  按 Ctrl+C 停止服务"
echo "=================================="

python3 app.py
