#!/usr/bin/env bash
# ============================================================
# 迁移脚本验证：从空数据库完整跑通 upgrade / downgrade
# ============================================================
# 用途：
#   成员 1 在提交任何模型改动前必须跑一次，确认迁移脚本可用。
#   对应《数据库设计》测试验证项：
#     "Alembic 迁移可以从空数据库完整执行，并可在测试环境升级"
#
# 用法：
#   bash deploy/verify_migration.sh
#
# 说明：
#   使用独立的临时数据库，不会影响 .env 中配置的正式库。
# ============================================================

set -uo pipefail

cd "$(dirname "$0")/.."

if [ -f ".venv/Scripts/python.exe" ]; then
    PY=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PY=".venv/bin/python"
else
    echo "[ERROR] 未找到虚拟环境 .venv"
    exit 1
fi

TMP_DB="./verify_migration_tmp.db"
# 用临时 SQLite 库验证，避免污染正式库
export DATABASE_URL="sqlite:///${TMP_DB#./}"

PASS=0
FAIL=0

ok()   { echo "  [PASS] $1"; PASS=$((PASS+1)); }
bad()  { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }

echo "============================================"
echo "  迁移脚本验证"
echo "============================================"
echo "临时数据库：$TMP_DB"
echo ""

# 清理上次残留
rm -f "$TMP_DB"

echo "=== 1. 空库执行 upgrade head ==="
if "$PY" -m alembic upgrade head > /tmp/mig_up.log 2>&1; then
    ok "upgrade head 执行成功"
else
    bad "upgrade head 执行失败"
    cat /tmp/mig_up.log
fi

echo ""
echo "=== 2. 检查建表结果 ==="
TABLE_COUNT=$("$PY" -c "
from app.core.database import engine
from sqlalchemy import inspect
names = [t for t in inspect(engine).get_table_names() if t != 'alembic_version']
print(len(names))
" 2>/dev/null | tail -1)

if [ "${TABLE_COUNT:-0}" -eq 13 ] 2>/dev/null; then
    ok "业务表数量正确：13 张"
else
    bad "业务表数量异常：${TABLE_COUNT:-未知}（期望 13）"
fi

echo ""
echo "=== 3. 重复执行 upgrade（幂等性）==="
if "$PY" -m alembic upgrade head > /tmp/mig_again.log 2>&1; then
    ok "重复 upgrade 无报错（幂等）"
else
    bad "重复 upgrade 报错"
    cat /tmp/mig_again.log
fi

echo ""
echo "=== 4. 回滚到空库 downgrade base ==="
if "$PY" -m alembic downgrade base > /tmp/mig_down.log 2>&1; then
    ok "downgrade base 执行成功"
else
    bad "downgrade base 执行失败"
    cat /tmp/mig_down.log
fi

echo ""
echo "=== 5. 确认表已清空 ==="
LEFT=$("$PY" -c "
from app.core.database import engine
from sqlalchemy import inspect
names = [t for t in inspect(engine).get_table_names() if t != 'alembic_version']
print(len(names))
" 2>/dev/null | tail -1)

if [ "${LEFT:-1}" -eq 0 ] 2>/dev/null; then
    ok "回滚后无残留业务表"
else
    bad "回滚后仍有 ${LEFT:-?} 张业务表"
fi

echo ""
echo "=== 6. 再次 upgrade（确认可重复部署）==="
if "$PY" -m alembic upgrade head > /tmp/mig_up2.log 2>&1; then
    ok "回滚后可再次升级"
else
    bad "回滚后再次升级失败"
    cat /tmp/mig_up2.log
fi

# 清理
rm -f "$TMP_DB"

echo ""
echo "============================================"
echo "  结果：PASS=$PASS  FAIL=$FAIL"
echo "============================================"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "[ERROR] 迁移脚本存在问题，请修复后再提交"
    exit 1
fi

echo "[OK] 迁移脚本验证通过"
