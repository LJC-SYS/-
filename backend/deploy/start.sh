#!/usr/bin/env bash
# ============================================================
# 一站式综合生活助手 · 后端启动脚本 (Linux / macOS / Git Bash)
# ============================================================
# 用法：
#   bash deploy/start.sh              # 前台启动（开发）
#   bash deploy/start.sh --daemon     # 后台启动（联调环境）
#
# 前置条件：
#   1. 已在 backend/ 下创建 .venv 并安装 requirements.txt
#   2. 已复制 .env.example 为 .env 并填好配置
# ============================================================

set -euo pipefail

cd "$(dirname "$0")/.."
BACKEND_DIR="$(pwd)"

# 按平台选择虚拟环境路径
if [ -f ".venv/Scripts/python.exe" ]; then
    PY=".venv/Scripts/python.exe"      # Windows (Git Bash)
elif [ -f ".venv/bin/python" ]; then
    PY=".venv/bin/python"              # Linux / macOS
else
    echo "[ERROR] 未找到虚拟环境 .venv"
    echo "        请先执行："
    echo "          python -m venv .venv"
    echo "          $PY -m pip install -r requirements.txt"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "[ERROR] 未找到 .env 配置文件"
    echo "        请先执行：cp .env.example .env"
    echo "        并修改 DATABASE_URL 和 JWT_SECRET_KEY"
    exit 1
fi

echo "============================================"
echo "  一站式综合生活助手 · 后端启动"
echo "============================================"
echo ""

echo "[1/3] 检查数据库迁移状态..."
"$PY" -m alembic current || echo "[WARN] 迁移状态检查失败，请确认数据库可连接"

echo ""
echo "[2/3] 执行数据库迁移..."
if ! "$PY" -m alembic upgrade head; then
    echo "[ERROR] 数据库迁移失败，中止启动"
    exit 1
fi

echo ""
echo "[3/3] 启动服务..."

if [ "${1:-}" = "--daemon" ]; then
    # 后台启动（联调环境用，供同事访问）
    mkdir -p logs
    echo "       后台模式，日志：logs/server.log"
    nohup "$PY" -m uvicorn app.main:app \
        --host 0.0.0.0 --port 8000 \
        > logs/server.log 2>&1 &
    echo $! > .server.pid
    sleep 2
    echo "       已启动，PID=$(cat .server.pid)"
    echo "       停止：kill \$(cat .server.pid)"
else
    # 前台启动（开发用，热重载）
    echo "       文档地址：http://127.0.0.1:8000/docs"
    echo "       健康检查：http://127.0.0.1:8000/health"
    echo "       按 Ctrl+C 停止"
    echo ""
    exec "$PY" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
fi
