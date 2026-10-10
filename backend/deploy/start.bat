#!/usr/bin/env bash
# ============================================================
# 一站式综合生活助手 · 后端启动脚本 (Windows)
# ============================================================
# 用法：
#   双击运行，或在 Git Bash 中执行 bash deploy/start.bat
#
# 前置条件：
#   1. 已在 backend/ 下创建 .venv 并安装 requirements.txt
#   2. 已复制 .env.example 为 .env 并填好配置
#   3. 已执行 alembic upgrade head
# ============================================================

@echo off
setlocal

cd /d "%~dp0.."

echo ============================================
echo   一站式综合生活助手 · 后端启动
echo ============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] 未找到虚拟环境 .venv
    echo         请先执行：
    echo           python -m venv .venv
    echo           .venv\Scripts\python.exe -m pip install -r requirements.txt
    exit /b 1
)

if not exist ".env" (
    echo [ERROR] 未找到 .env 配置文件
    echo         请先执行： copy .env.example .env
    echo         并修改 DATABASE_URL 和 JWT_SECRET_KEY
    exit /b 1
)

echo [1/3] 检查数据库迁移状态...
".venv\Scripts\python.exe" -m alembic current
if errorlevel 1 (
    echo [WARN] 迁移状态检查失败，请确认数据库可连接
)

echo.
echo [2/3] 执行数据库迁移...
".venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 (
    echo [ERROR] 数据库迁移失败，中止启动
    exit /b 1
)

echo.
echo [3/3] 启动服务...
echo       文档地址：http://127.0.0.1:8000/docs
echo       健康检查：http://127.0.0.1:8000/health
echo       按 Ctrl+C 停止
echo.

".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

endlocal
