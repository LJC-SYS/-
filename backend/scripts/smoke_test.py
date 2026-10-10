"""接口冒烟测试脚本。

用途：第 1 周技术验证 + 后续回归。不依赖 pytest，用 TestClient 直接跑。
运行：
    ./.venv/Scripts/python.exe scripts/smoke_test.py
"""

import sys
import uuid
from pathlib import Path

# 保证能 import app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)
PASS, FAIL = 0, 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")


def body(r):
    try:
        return r.json()
    except Exception:
        return {}


print("\n=== 1. 健康检查 ===")
r = client.get("/health")
b = body(r)
check("HTTP 200", r.status_code == 200, str(r.status_code))
check("code == 0", b.get("code") == 0, str(b))
check("统一响应体字段齐全",
      all(k in b for k in ("code", "message", "data", "request_id", "timestamp")), str(list(b.keys())))
check("X-Request-Id 响应头存在", "X-Request-Id" in r.headers)

print("\n=== 2. 注册 ===")
uname = f"alice_{uuid.uuid4().hex[:6]}"
reg = {
    "username": uname,
    "password": "abc12345",
    "email": f"{uname}@example.com",
    "nickname": "小爱",
}
r = client.post("/api/v1/auth/register", json=reg)
b = body(r)
check("注册成功 code == 0", b.get("code") == 0, str(b))
data = b.get("data") or {}
access = data.get("access_token")
refresh = data.get("refresh_token")
check("返回 access_token", bool(access))
check("返回 refresh_token", bool(refresh))
check("expires_in == 7200", data.get("expires_in") == 7200, str(data.get("expires_in")))
check("token_type == Bearer", data.get("token_type") == "Bearer")

print("\n=== 3. 注册参数校验 (422) ===")
r = client.post("/api/v1/auth/register", json={"username": "ab", "password": "123"})
b = body(r)
check("弱参数返回 422", r.status_code == 422, str(r.status_code))
check("业务码 1001", b.get("code") == 1001, str(b.get("code")))

print("\n=== 4. 重复用户名 ===")
r = client.post("/api/v1/auth/register", json=reg)
b = body(r)
check("返回 1103 用户名已占用", b.get("code") == 1103, str(b))
check("HTTP 200 (业务错误用 200)", r.status_code == 200, str(r.status_code))

print("\n=== 5. 登录（三种凭证） ===")
for label, account in [("用户名", uname), ("邮箱", reg["email"])]:
    r = client.post("/api/v1/auth/login", json={"account": account, "password": "abc12345"})
    b = body(r)
    check(f"{label}登录成功", b.get("code") == 0, str(b))

print("\n=== 6. 密码错误 ===")
r = client.post("/api/v1/auth/login", json={"account": uname, "password": "wrongpass1"})
b = body(r)
check("返回 1102 账号或密码错误", b.get("code") == 1102, str(b))

print("\n=== 7. 未授权访问 ===")
r = client.get("/api/v1/users/me")
b = body(r)
check("无 Token 返回 401", r.status_code == 401, str(r.status_code))
check("业务码 1002", b.get("code") == 1002, str(b.get("code")))

r = client.get("/api/v1/users/me", headers={"Authorization": "Bearer bad.token.here"})
b = body(r)
check("无效 Token 返回 1004", b.get("code") == 1004, str(b.get("code")))

print("\n=== 8. 个人资料 ===")
h = {"Authorization": f"Bearer {access}"}
r = client.get("/api/v1/users/me", headers=h)
b = body(r)
d = b.get("data") or {}
check("获取资料成功", b.get("code") == 0, str(b))
check("username 正确", d.get("username") == uname, str(d.get("username")))
check("nickname 正确", d.get("nickname") == "小爱", str(d.get("nickname")))
check("points_balance == 0", d.get("points_balance") == 0, str(d.get("points_balance")))
check("包含统计字段", all(k in d for k in ("continuous_days", "total_checkin_days", "badge_count")), str(list(d.keys())))

print("\n=== 9. 修改资料 ===")
r = client.patch("/api/v1/users/me", headers=h, json={"nickname": "新昵称"})
b = body(r)
check("修改成功", b.get("code") == 0, str(b))
check("昵称已更新", (b.get("data") or {}).get("nickname") == "新昵称")

print("\n=== 10. 用户设置 ===")
r = client.get("/api/v1/users/me/settings", headers=h)
b = body(r)
d = b.get("data") or {}
check("读取设置成功", b.get("code") == 0, str(b))
check("默认 theme_mode == system", d.get("theme_mode") == "system", str(d))

r = client.put("/api/v1/users/me/settings", headers=h,
               json={"theme_mode": "dark", "notification_enabled": False,
                     "language": "zh-CN", "weather_city_code": "101090701"})
b = body(r)
check("更新设置成功", b.get("code") == 0, str(b))
check("theme_mode == dark", (b.get("data") or {}).get("theme_mode") == "dark")

r = client.put("/api/v1/users/me/settings", headers=h,
               json={"theme_mode": "rainbow", "notification_enabled": True, "language": "zh-CN"})
b = body(r)
check("非法 theme_mode 被拒", r.status_code == 422 and b.get("code") == 1001, str(b.get("code")))

print("\n=== 11. 刷新 Token（轮换） ===")
r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
b = body(r)
check("刷新成功", b.get("code") == 0, str(b))
new_access = (b.get("data") or {}).get("access_token")
new_refresh = (b.get("data") or {}).get("refresh_token")
check("返回新 access_token", bool(new_access) and new_access != access)
check("返回新 refresh_token", bool(new_refresh) and new_refresh != refresh)

print("\n=== 12. 旧 refresh 复用应被拒（防盗用） ===")
r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
b = body(r)
check("旧 refresh 返回 1108", b.get("code") == 1108, str(b))

print("\n=== 13. 新 access 仍可用 ===")
h2 = {"Authorization": f"Bearer {new_access}"}
r = client.get("/api/v1/users/me", headers=h2)
b = body(r)
check("新 access 可用", b.get("code") == 0, str(b))

print("\n=== 14. 登出 ===")
r = client.post("/api/v1/auth/logout", headers=h2, json={"refresh_token": new_refresh})
b = body(r)
check("登出成功", b.get("code") == 0, str(b))
r = client.post("/api/v1/auth/logout", headers=h2, json={})
b = body(r)
check("登出幂等（重复调用仍成功）", b.get("code") == 0, str(b))

print("\n=== 15. 修改密码 ===")
r = client.post("/api/v1/auth/login", json={"account": uname, "password": "abc12345"})
b = body(r)
acc3 = (b.get("data") or {}).get("access_token")
h3 = {"Authorization": f"Bearer {acc3}"}
r = client.post("/api/v1/users/me/password", headers=h3,
                json={"old_password": "wrongold1", "new_password": "xyz98765"})
b = body(r)
check("原密码错误返回 1112", b.get("code") == 1112, str(b))

r = client.post("/api/v1/users/me/password", headers=h3,
                json={"old_password": "abc12345", "new_password": "xyz98765"})
b = body(r)
check("改密成功", b.get("code") == 0, str(b))

r = client.post("/api/v1/auth/login", json={"account": uname, "password": "xyz98765"})
b = body(r)
check("新密码可登录", b.get("code") == 0, str(b))
r = client.post("/api/v1/auth/login", json={"account": uname, "password": "abc12345"})
b = body(r)
check("旧密码失效", b.get("code") == 1102, str(b))

print("\n=== 16. 404 路径 ===")
r = client.get("/api/v1/not-exist-path")
b = body(r)
check("未知路径返回 404", r.status_code == 404, str(r.status_code))
check("统一响应体仍生效", "code" in b, str(b))

print(f"\n{'='*46}")
print(f"  冒烟测试结果：PASS={PASS}  FAIL={FAIL}")
print(f"{'='*46}\n")

sys.exit(1 if FAIL else 0)
