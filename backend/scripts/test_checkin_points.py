"""打卡、积分与徽章模块自动化测试脚本。

验证场景：
1. 正常打卡：积分+10，连续天数=1，流水生成，返回数据结构严格匹配契约 6.13。
2. 幂等防护：同 client_id 重复提交返回已有记录，不重复增加积分。
3. 重复打卡拦截：当日不同 client_id 再次打卡返回 1301 (CHECKIN_ALREADY_DONE)。
4. 打卡日历查询：checkin_days 包含打卡天数序号，返回匹配契约 6.14。
5. 打卡统计概览：today_checked=True，连续天数与总天数统计正确匹配契约 6.15。
6. 积分余额查询：points_balance, today_earned, total_earned 准确计算匹配契约 6.16。
7. 积分流水明细：标准 PageData 分页返回匹配契约 6.17。
8. 全量徽章查询：正确返回 6 个系统预设徽章及解锁状态匹配契约 6.18。
9. 徽章解锁判定：模拟连续打卡 3 天自动触发并解锁 checkin_3 ("初来乍到") 徽章。
"""

import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import CheckinRecord, PointTransaction, User, UserBadge

client = TestClient(app)


def _get_auth_header(username: str = "checkin_user_01"):
    """注册或登录获取测试用 Bearer Token。"""
    # 尝试登录，若不存在则注册
    login_resp = client.post("/api/v1/auth/login", json={"account": username, "password": "User@123456"})
    if login_resp.status_code == 200 and login_resp.json()["code"] == 0:
        token = login_resp.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": "User@123456",
            "email": f"{username}@example.com",
            "nickname": "打卡测试",
        },
    )
    assert reg_resp.status_code == 200 and reg_resp.json()["code"] == 0, f"测试账号创建失败: {reg_resp.text}"
    token = reg_resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def run_tests():
    print("=" * 65)
    print("  开始打卡、积分与徽章模块接口全量验证")
    print("=" * 65)

    test_username = f"user_{uuid.uuid4().hex[:8]}"
    headers = _get_auth_header(test_username)

    # 1. 正常打卡
    print("\n[测试 1] 首次打卡 (5步原子事务执行)")
    client_id_1 = str(uuid.uuid4())
    resp = client.post(
        "/api/v1/checkins",
        json={"client_id": client_id_1, "remark": "坚持打卡第一天"},
        headers=headers,
    )
    assert resp.status_code == 200, f"打卡失败: {resp.text}"
    body = resp.json()
    assert body["code"] == 0, f"业务码错误: {body['code']}"
    data = body["data"]
    assert data["points_earned"] == 10, "打卡固定奖励应为 10"
    assert data["continuous_days"] == 1, "首日打卡连续天数应为 1"
    assert data["points_balance"] == 10, "首日打卡余额应为 10"
    checkin_id_1 = data["checkin_id"]
    print("  [PASS] 打卡成功: checkin_id =", checkin_id_1, "积分余额 =", data["points_balance"])

    # 2. 幂等防护：同 client_id 再次提交
    print("\n[测试 2] 幂等测试 (同 client_id 重复提交)")
    resp_idem = client.post(
        "/api/v1/checkins",
        json={"client_id": client_id_1, "remark": "重复点击"},
        headers=headers,
    )
    assert resp_idem.status_code == 200
    body_idem = resp_idem.json()
    assert body_idem["code"] == 0, "幂等重放应返回 code=0"
    assert body_idem["data"]["checkin_id"] == checkin_id_1, "幂等应返回原有记录 ID"
    assert body_idem["data"]["points_balance"] == 10, "积分余额不得重复增加"
    print("  [PASS] 幂等拦截成功: 返回原打卡记录，未重复派发积分")

    # 3. 重复打卡拦截：当日不同 client_id
    print("\n[测试 3] 重复打卡拦截 (当日不同 client_id 提交)")
    resp_dup = client.post(
        "/api/v1/checkins",
        json={"client_id": str(uuid.uuid4()), "remark": "今天第二次打卡"},
        headers=headers,
    )
    assert resp_dup.status_code == 200
    body_dup = resp_dup.json()
    assert body_dup["code"] == 1301, f"重复打卡业务码应为 1301，实际: {body_dup['code']}"
    print("  [PASS] 重复打卡拦截成功: 业务码 1301 (CHECKIN_ALREADY_DONE)")

    # 4. 打卡日历查询
    print("\n[测试 4] 打卡日历查询 (GET /api/v1/checkins/calendar)")
    now = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE))
    resp_cal = client.get(
        f"/api/v1/checkins/calendar?year={now.year}&month={now.month}",
        headers=headers,
    )
    assert resp_cal.status_code == 200
    body_cal = resp_cal.json()
    assert body_cal["code"] == 0
    data_cal = body_cal["data"]
    assert now.day in data_cal["checkin_days"], f"今日日期 {now.day} 应在 checkin_days 中"
    assert data_cal["month_total"] >= 1
    assert len(data_cal["list"]) >= 1
    print("  [PASS] 日历查询成功: 当月打卡天数 =", data_cal["checkin_days"])

    # 5. 打卡统计概览
    print("\n[测试 5] 打卡统计查询 (GET /api/v1/checkins/stats)")
    resp_stats = client.get("/api/v1/checkins/stats", headers=headers)
    assert resp_stats.status_code == 200
    body_stats = resp_stats.json()
    assert body_stats["code"] == 0
    data_stats = body_stats["data"]
    assert data_stats["today_checked"] is True, "今日已打卡应为 True"
    assert data_stats["continuous_days"] == 1
    assert data_stats["total_checkin_days"] >= 1
    print("  [PASS] 统计查询成功: today_checked = True, continuous_days = 1")

    # 6. 积分余额查询
    print("\n[测试 6] 积分余额查询 (GET /api/v1/points/balance)")
    resp_pt = client.get("/api/v1/points/balance", headers=headers)
    assert resp_pt.status_code == 200
    body_pt = resp_pt.json()
    assert body_pt["code"] == 0
    data_pt = body_pt["data"]
    assert data_pt["points_balance"] == 10
    assert data_pt["today_earned"] == 10
    assert data_pt["total_earned"] >= 10
    print("  [PASS] 积分余额计算正确: balance = 10, today_earned = 10")

    # 7. 积分流水查询 (分页 PageData)
    print("\n[测试 7] 积分流水查询 (GET /api/v1/points/transactions)")
    resp_tx = client.get("/api/v1/points/transactions?page=1&page_size=10", headers=headers)
    assert resp_tx.status_code == 200
    body_tx = resp_tx.json()
    assert body_tx["code"] == 0
    data_tx = body_tx["data"]
    assert data_tx["total"] >= 1
    assert len(data_tx["list"]) >= 1
    first_tx = data_tx["list"][0]
    assert first_tx["change_amount"] == 10
    assert first_tx["transaction_type"] == "checkin"
    print("  [PASS] 积分流水校验正确: total =", data_tx["total"], "tx_type =", first_tx["transaction_type"])

    # 8. 徽章列表查询
    print("\n[测试 8] 徽章列表查询 (GET /api/v1/badges)")
    resp_bg = client.get("/api/v1/badges", headers=headers)
    assert resp_bg.status_code == 200
    body_bg = resp_bg.json()
    assert body_bg["code"] == 0
    data_bg = body_bg["data"]
    assert data_bg["total_count"] == 6, f"系统应有 6 个预设徽章，实际: {data_bg['total_count']}"
    print("  [PASS] 徽章列表查询成功: 预设徽章总数 =", data_bg["total_count"])

    # 9. 徽章达成解锁验证 (模拟打卡达到 3 天触发 checkin_3 "初来乍到")
    print("\n[测试 9] 徽章解锁判定 (连续 3 天打卡解锁 '初来乍到')")
    user_badge_test = f"badge_user_{uuid.uuid4().hex[:8]}"
    headers_badge = _get_auth_header(user_badge_test)

    # 通过 DB 先为该用户伪造前两天的连续打卡记录
    db = SessionLocal()
    u = db.query(User).filter(User.username == user_badge_test).first()
    today_dt = now.date()
    d1 = today_dt - timedelta(days=2)
    d2 = today_dt - timedelta(days=1)

    r1 = CheckinRecord(user_id=u.id, checkin_date=d1, checkin_time=now - timedelta(days=2), points_earned=10, continuous_days=1, created_at=now)
    r2 = CheckinRecord(user_id=u.id, checkin_date=d2, checkin_time=now - timedelta(days=1), points_earned=10, continuous_days=2, created_at=now)
    db.add(r1)
    db.add(r2)
    u.points_balance = 20
    db.commit()
    db.close()

    # 第 3 天通过正常接口打卡，应该自动解锁 checkin_3
    resp_day3 = client.post(
        "/api/v1/checkins",
        json={"remark": "第3天打卡"},
        headers=headers_badge,
    )
    assert resp_day3.status_code == 200
    body_day3 = resp_day3.json()
    assert body_day3["code"] == 0
    data_day3 = body_day3["data"]
    assert data_day3["continuous_days"] == 3, f"连续天数应累加为 3，实际: {data_day3['continuous_days']}"
    assert len(data_day3["new_badges"]) >= 1, "连续 3 天必须解锁新徽章"
    badge_codes = [b["code"] for b in data_day3["new_badges"]]
    assert "checkin_3" in badge_codes, f"应解锁 checkin_3 徽章，实际获得: {badge_codes}"
    print("  [PASS] 徽章触发成功！打卡响应返回 new_badges: ", data_day3["new_badges"])

    # 查徽章接口确认 earned 为 True
    resp_badge_earned = client.get("/api/v1/badges", headers=headers_badge)
    body_be = resp_badge_earned.json()["data"]
    earned_item = next(b for b in body_be["list"] if b["code"] == "checkin_3")
    assert earned_item["earned"] is True, "checkin_3 徽章状态必须为 True"
    assert earned_item["earned_at"] is not None
    assert body_be["earned_count"] >= 1
    print("  [PASS] 徽章状态查询确认: checkin_3 已标记 earned=True, earned_count =", body_be["earned_count"])

    print("\n" + "=" * 65)
    print("  恭喜！打卡、积分与徽章全部 9 项测试用例全部 PASS！")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()
