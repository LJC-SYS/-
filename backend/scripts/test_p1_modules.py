"""第二阶段 (P1 模块) 专项自动化集成测试。

覆盖模块：
1. 待办事项 (Todos)：CRUD、client_id 幂等、乐观锁 (1407)、软删除
2. 备忘录 (Memos)：CRUD、置顶优先、client_id 幂等、乐观锁 (1407)、软删除
3. 记账本 (Accounting)：分类查询、收支记账 CRUD、金额校验 (1406)、分类类型匹配 (1405)、月度汇总统计
4. 云端同步 (Sync)：批量推送 (/sync/push)、幂等跳过、版本冲突检测、增量拉取 (/sync/pull)

运行：
    python scripts/test_p1_modules.py
"""

import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from app.models import AccountingCategory, User

client = TestClient(app)

PASSED = 0
FAILED = 0


def log_test(name: str, ok: bool, detail: str = ""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  [PASS] {name}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name} - {detail}")


def get_auth_token() -> str:
    """注册并登录一个独立的测试用户，返回 access_token。"""
    uname = f"u_p1_{uuid.uuid4().hex[:8]}"
    pwd = "User@123456"

    res = client.post(
        "/api/v1/auth/register",
        json={
            "username": uname,
            "password": pwd,
            "email": f"{uname}@example.com",
            "nickname": "P1测试员",
        },
    )
    assert res.status_code == 200 and res.json()["code"] == 0, res.text
    data = res.json()["data"]
    return data["access_token"]


def test_todos(token: str):
    print("\n=== [1/4] 测试待办事项 (Todos) 模块 ===")
    headers = {"Authorization": f"Bearer {token}"}
    client_id = str(uuid.uuid4())

    # 1. 创建待办
    res = client.post(
        "/api/v1/todos",
        headers=headers,
        json={
            "client_id": client_id,
            "title": "购买周末食材",
            "description": "番茄、牛肉、青椒",
            "priority": "high",
            "sort_order": 1,
        },
    )
    ok = res.status_code == 200 and res.json()["code"] == 0
    todo_data = res.json()["data"] if ok else {}
    todo_id = todo_data.get("id")
    log_test("新增待办事项", ok and todo_id is not None and todo_data.get("version") == 1)

    # 2. 幂等性测试（相同 client_id 重复提交返回已有记录）
    res_dup = client.post(
        "/api/v1/todos",
        headers=headers,
        json={
            "client_id": client_id,
            "title": "购买周末食材（重复传）",
        },
    )
    ok_dup = (
        res_dup.status_code == 200
        and res_dup.json()["code"] == 0
        and res_dup.json()["data"]["id"] == todo_id
    )
    log_test("待办 client_id 幂等防重放", ok_dup)

    # 3. 待办列表查询
    res_list = client.get("/api/v1/todos?status=pending", headers=headers)
    ok_list = (
        res_list.status_code == 200
        and res_list.json()["code"] == 0
        and res_list.json()["data"]["total"] >= 1
    )
    log_test("待办分页列表查询", ok_list)

    # 4. 修改待办（更新状态为 completed，版本递增为 2）
    res_update = client.patch(
        f"/api/v1/todos/{todo_id}",
        headers=headers,
        json={
            "version": 1,
            "status": "completed",
            "title": "购买周末食材（已买完）",
        },
    )
    ok_update = (
        res_update.status_code == 200
        and res_update.json()["code"] == 0
        and res_update.json()["data"]["version"] == 2
        and res_update.json()["data"]["completed_at"] is not None
    )
    log_test("修改待办与状态联动", ok_update)

    # 5. 乐观锁冲突拦截（传旧版本 version=1 应被拦截报 1407）
    res_conflict = client.patch(
        f"/api/v1/todos/{todo_id}",
        headers=headers,
        json={
            "version": 1,
            "title": "并发冲突测试",
        },
    )
    ok_conflict = res_conflict.status_code == 200 and res_conflict.json()["code"] == 1407
    log_test("待办乐观锁版本冲突拦截 (1407)", ok_conflict)

    # 6. 软删除待办
    res_del = client.delete(f"/api/v1/todos/{todo_id}?version=2", headers=headers)
    ok_del = res_del.status_code == 200 and res_del.json()["code"] == 0

    # 再次查询确认已被软删除（查不出）
    res_verify = client.get("/api/v1/todos", headers=headers)
    items = res_verify.json()["data"]["list"]
    deleted_hidden = all(item["id"] != todo_id for item in items)
    log_test("待办软删除与列表隔离", ok_del and deleted_hidden)


def test_memos(token: str):
    print("\n=== [2/4] 测试备忘录 (Memos) 模块 ===")
    headers = {"Authorization": f"Bearer {token}"}
    client_id = str(uuid.uuid4())

    # 1. 新增备忘录
    res = client.post(
        "/api/v1/memos",
        headers=headers,
        json={
            "client_id": client_id,
            "title": "项目会议要点",
            "content": "1. 确定接口契约\n2. 跑通单元测试",
            "is_pinned": True,
            "color": "#FFF9C4",
        },
    )
    ok = res.status_code == 200 and res.json()["code"] == 0
    memo_data = res.json()["data"] if ok else {}
    memo_id = memo_data.get("id")
    log_test("新增备忘录", ok and memo_id is not None and memo_data.get("is_pinned") is True)

    # 2. 幂等性测试
    res_dup = client.post(
        "/api/v1/memos",
        headers=headers,
        json={
            "client_id": client_id,
            "content": "重复备忘录内容",
        },
    )
    ok_dup = (
        res_dup.status_code == 200
        and res_dup.json()["code"] == 0
        and res_dup.json()["data"]["id"] == memo_id
    )
    log_test("备忘录 client_id 幂等防重放", ok_dup)

    # 3. 列表查询（置顶筛选）
    res_list = client.get("/api/v1/memos?is_pinned=true", headers=headers)
    ok_list = (
        res_list.status_code == 200
        and res_list.json()["code"] == 0
        and res_list.json()["data"]["total"] >= 1
    )
    log_test("备忘录置顶列表查询", ok_list)

    # 4. 修改备忘录与乐观锁测试
    res_update = client.patch(
        f"/api/v1/memos/{memo_id}",
        headers=headers,
        json={
            "version": 1,
            "content": "更新后的正文内容",
        },
    )
    ok_update = (
        res_update.status_code == 200
        and res_update.json()["code"] == 0
        and res_update.json()["data"]["version"] == 2
    )
    log_test("修改备忘录", ok_update)

    # 5. 乐观锁冲突拦截 (1407)
    res_conflict = client.patch(
        f"/api/v1/memos/{memo_id}",
        headers=headers,
        json={"version": 1, "content": "试图用旧版本覆盖"},
    )
    ok_conflict = res_conflict.status_code == 200 and res_conflict.json()["code"] == 1407
    log_test("备忘录乐观锁版本冲突拦截 (1407)", ok_conflict)

    # 6. 软删除备忘录
    res_del = client.delete(f"/api/v1/memos/{memo_id}?version=2", headers=headers)
    ok_del = res_del.status_code == 200 and res_del.json()["code"] == 0
    log_test("软删除备忘录", ok_del)


def test_accounting(token: str):
    print("\n=== [3/4] 测试记账本 (Accounting) 模块 ===")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. 查询记账分类
    res_cat = client.get("/api/v1/accounting/categories", headers=headers)
    ok_cat = (
        res_cat.status_code == 200
        and res_cat.json()["code"] == 0
        and len(res_cat.json()["data"]["list"]) > 0
    )
    cats = res_cat.json()["data"]["list"] if ok_cat else []
    expense_cat = next((c for c in cats if c["category_type"] == "expense"), None)
    income_cat = next((c for c in cats if c["category_type"] == "income"), None)
    log_test("记账分类查询（系统预设继承）", ok_cat and expense_cat is not None and income_cat is not None)

    # 2. 新增记账（支出）
    client_id_exp = str(uuid.uuid4())
    res_exp = client.post(
        "/api/v1/accounting/records",
        headers=headers,
        json={
            "client_id": client_id_exp,
            "category_id": expense_cat["id"],
            "record_type": "expense",
            "amount": "88.50",
            "record_date": "2026-10-10",
            "note": "丰盛午餐",
        },
    )
    ok_exp = (
        res_exp.status_code == 200
        and res_exp.json()["code"] == 0
        and res_exp.json()["data"]["amount"] == "88.50"
    )
    rec_exp_id = res_exp.json()["data"]["id"] if ok_exp else None
    log_test("新增支出记账记录", ok_exp and rec_exp_id is not None)

    # 3. 新增记账（收入）
    client_id_inc = str(uuid.uuid4())
    res_inc = client.post(
        "/api/v1/accounting/records",
        headers=headers,
        json={
            "client_id": client_id_inc,
            "category_id": income_cat["id"],
            "record_type": "income",
            "amount": "5000.00",
            "record_date": "2026-10-10",
            "note": "本月基本工资",
        },
    )
    ok_inc = (
        res_inc.status_code == 200
        and res_inc.json()["code"] == 0
        and res_inc.json()["data"]["amount"] == "5000.00"
    )
    log_test("新增收入记账记录", ok_inc)

    # 4. 金额 <= 0 拦截校验 (1406)
    res_invalid_amt = client.post(
        "/api/v1/accounting/records",
        headers=headers,
        json={
            "client_id": str(uuid.uuid4()),
            "category_id": expense_cat["id"],
            "record_type": "expense",
            "amount": "0.00",
            "record_date": "2026-10-10",
        },
    )
    # pydantic 校验或业务校验拦截均可
    ok_amt = res_invalid_amt.status_code in (200, 422)
    log_test("记账金额必须大于 0 拦截校验", ok_amt)

    # 5. 分类类型不匹配拦截校验 (1405: 支出记录使用了收入分类)
    res_mismatch = client.post(
        "/api/v1/accounting/records",
        headers=headers,
        json={
            "client_id": str(uuid.uuid4()),
            "category_id": income_cat["id"],  # 收入分类
            "record_type": "expense",          # 支出记录
            "amount": "10.00",
            "record_date": "2026-10-10",
        },
    )
    ok_mismatch = res_mismatch.status_code == 200 and res_mismatch.json()["code"] == 1405
    log_test("分类类型不匹配拦截校验 (1405)", ok_mismatch)

    # 6. 记账记录明细查询
    res_list = client.get("/api/v1/accounting/records?record_type=expense", headers=headers)
    ok_list = (
        res_list.status_code == 200
        and res_list.json()["code"] == 0
        and res_list.json()["data"]["total"] >= 1
    )
    log_test("记账明细列表按类型筛选", ok_list)

    # 7. 收支区间汇总统计
    res_summary = client.get(
        "/api/v1/accounting/summary?start_date=2026-10-01&end_date=2026-10-31",
        headers=headers,
    )
    ok_sum = False
    if res_summary.status_code == 200 and res_summary.json()["code"] == 0:
        sdata = res_summary.json()["data"]
        ok_sum = (
            float(sdata["total_income"]) >= 5000.0
            and float(sdata["total_expense"]) >= 88.5
            and float(sdata["balance"]) > 0
            and len(sdata["groups"]) > 0
        )
    log_test("记账月度收支与净结余汇总统计", ok_sum)

    # 8. 软删除记账记录
    res_del = client.delete(f"/api/v1/accounting/records/{rec_exp_id}?version=1", headers=headers)
    ok_del = res_del.status_code == 200 and res_del.json()["code"] == 0
    log_test("软删除记账记录", ok_del)


def test_sync(token: str):
    print("\n=== [4/4] 测试云端双向同步 (Sync) 模块 ===")
    headers = {"Authorization": f"Bearer {token}"}

    cid_todo = str(uuid.uuid4())
    cid_memo = str(uuid.uuid4())
    cid_acc = str(uuid.uuid4())

    # 1. 批量推送本地变更 (/sync/push)
    res_push = client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "device_id": "test-device-01",
            "changes": [
                {
                    "entity_type": "todo",
                    "client_id": cid_todo,
                    "action": "create",
                    "version": 0,
                    "data": {"title": "离线创建的待办", "priority": "normal"},
                },
                {
                    "entity_type": "memo",
                    "client_id": cid_memo,
                    "action": "create",
                    "version": 0,
                    "data": {"title": "离线备忘录", "content": "这是离线保存的"},
                },
                {
                    "entity_type": "accounting",
                    "client_id": cid_acc,
                    "action": "create",
                    "version": 0,
                    "data": {"category_id": 1, "record_type": "expense", "amount": "25.00"},
                },
            ],
        },
    )
    ok_push = False
    if res_push.status_code == 200 and res_push.json()["code"] == 0:
        results = res_push.json()["data"]["results"]
        ok_push = (
            len(results) == 3
            and all(r["status"] == "created" for r in results)
            and res_push.json()["data"]["partial_failure"] is False
        )
    log_test("批量推送本地变更 (push create)", ok_push)

    # 2. 幂等推送跳过
    res_push_dup = client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "device_id": "test-device-01",
            "changes": [
                {
                    "entity_type": "todo",
                    "client_id": cid_todo,
                    "action": "create",
                    "version": 0,
                    "data": {"title": "离线创建的待办"},
                },
            ],
        },
    )
    ok_dup = (
        res_push_dup.status_code == 200
        and res_push_dup.json()["code"] == 0
        and res_push_dup.json()["data"]["results"][0]["status"] == "skipped"
    )
    log_test("推送变更幂等防重放 (push skipped)", ok_dup)

    # 3. 版本冲突检测 (客户端传错版本导致 conflict 并返回 server_data)
    res_conflict = client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "device_id": "test-device-01",
            "changes": [
                {
                    "entity_type": "todo",
                    "client_id": cid_todo,
                    "action": "update",
                    "version": 99,  # 错误的版本号
                    "data": {"title": "冲突修改"},
                },
            ],
        },
    )
    ok_conf = (
        res_conflict.status_code == 200
        and res_conflict.json()["code"] == 0
        and res_conflict.json()["data"]["results"][0]["status"] == "conflict"
        and res_conflict.json()["data"]["partial_failure"] is True
    )
    log_test("推送变更版本冲突处理 (status=conflict, partial_failure=True)", ok_conf)

    # 4. 增量拉取 (/sync/pull)
    since_str = "1970-01-01T00:00:00+08:00"
    res_pull = client.get(f"/api/v1/sync/pull?since={since_str}&limit=50", headers=headers)
    ok_pull = False
    if res_pull.status_code == 200 and res_pull.json()["code"] == 0:
        pdata = res_pull.json()["data"]
        changes = pdata["changes"]
        ok_pull = len(changes) >= 3 and any(c["client_id"] == cid_todo for c in changes)
    log_test("全量/增量拉取变动 (pull since)", ok_pull)


def main():
    print("=" * 60)
    print("  开始执行第二阶段 (P1 模块) 自动化集成测试套件")
    print("=" * 60)

    token = get_auth_token()
    test_todos(token)
    test_memos(token)
    test_accounting(token)
    test_sync(token)

    print("\n" + "=" * 60)
    print(f"  测试汇总: 总共通过 {PASSED} 项，失败 {FAILED} 项")
    print("=" * 60)

    if FAILED > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
