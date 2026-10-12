"""天气模块自动化测试脚本。

验证场景：
1. 首次查询：正常获取天气，写入缓存 (from_cache=False, degraded=False)。
2. 二次查询：命中缓存 (from_cache=True, degraded=False)。
3. 第三方故障降级：有历史缓存时，优雅降级返回 (from_cache=True, degraded=True, code=0, HTTP 200)。
4. 第三方故障且无缓存：抛出 1204 业务错误码 (WEATHER_NO_CACHE)。
5. 天气预报查询：指定天数正确返回列表。
6. 预报参数校验：days 超出范围返回 422。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app
from app.integrations.weather_client import weather_client
from app.core.database import SessionLocal
from app.models.sync import WeatherCache

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("  开始天气模块接口与降级策略验证")
    print("=" * 60)

    test_city = "101090701" # 沧州
    test_city_name = "沧州"

    # 清理历史可能存在的缓存
    db = SessionLocal()
    db.query(WeatherCache).filter(WeatherCache.location_code == test_city).delete()
    db.commit()
    db.close()

    # 1. 首次查询实时天气
    print("\n[测试 1] 首次查询实时天气 (未命中缓存)")
    weather_client.set_simulate_failure(False)
    resp = client.get(f"/api/v1/weather/current?city_code={test_city}&city_name={test_city_name}")
    assert resp.status_code == 200, f"状态码异常: {resp.status_code}"
    body = resp.json()
    assert body["code"] == 0, f"业务码异常: {body['code']}"
    data = body["data"]
    assert data["city_code"] == test_city
    assert data["city_name"] == "沧州"
    assert data["from_cache"] is False, "首次查询不应该来自缓存"
    assert data["degraded"] is False, "首次正常请求不应该标记降级"
    assert "temperature" in data
    print("  [PASS] 首次查询成功: 温度 =", data["temperature"], "天气 =", data["weather_text"])

    # 2. 第二次查询（应该命中缓存）
    print("\n[测试 2] 二次查询实时天气 (命中有效缓存)")
    resp = client.get(f"/api/v1/weather/current?city_code={test_city}&city_name={test_city_name}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["from_cache"] is True, "二次查询必须命中缓存"
    assert data["degraded"] is False, "正常命中缓存不应降级"
    print("  [PASS] 缓存命中成功: from_cache = True, degraded = False")

    # 3. 模拟第三方服务异常（有过期缓存时的优雅降级）
    print("\n[测试 3] 模拟第三方故障 + 存在过期缓存 (触发优雅降级)")
    db = SessionLocal()
    c = db.query(WeatherCache).filter(WeatherCache.location_code == test_city).first()
    c.expires_at = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE)) - timedelta(minutes=5)
    db.commit()
    db.close()

    weather_client.set_simulate_failure(True)
    resp = client.get(f"/api/v1/weather/current?city_code={test_city}&city_name={test_city_name}")
    assert resp.status_code == 200, "降级必须返回 HTTP 200，绝不能返回 500"
    body = resp.json()
    assert body["code"] == 0, "降级必须返回 code=0"
    data = body["data"]
    assert data["from_cache"] is True, "降级必须标明来自缓存"
    assert data["degraded"] is True, "降级必须标明 degraded=True"
    print("  [PASS] 优雅降级验证成功: 成功捕获故障并返回旧缓存，degraded = True, HTTP 200")

    # 4. 模拟第三方服务异常 + 无历史缓存（必须返回 1204 错误码）
    print("\n[测试 4] 模拟第三方故障 + 无缓存 (返回 1204)")
    uncached_city = "999999999"
    resp = client.get(f"/api/v1/weather/current?city_code={uncached_city}")
    assert resp.status_code == 200, "业务失败仍返回 200"
    body = resp.json()
    assert body["code"] == 1204, f"无缓存且失败应返回 1204，实际: {body['code']}"
    print("  [PASS] 无缓存降级拦截成功: 业务码 1204 (WEATHER_NO_CACHE)")

    # 恢复正常客户端状态
    weather_client.set_simulate_failure(False)

    # 5. 查询未来 3 天预报
    print("\n[测试 5] 查询未来 3 天天气预报")
    resp = client.get(f"/api/v1/weather/forecast?city_code={test_city}&days=3&city_name={test_city_name}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert len(data["list"]) == 3, f"预报天数应为 3，实际: {len(data['list'])}"
    for item in data["list"]:
        assert "date" in item
        assert "weather_text" in item
        assert "temp_max" in item
        assert "temp_min" in item
    print("  [PASS] 天气预报查询成功: 返回天数 =", len(data["list"]))

    # 6. 预报 days 参数校验（例如传 10 天，超出 1~7 范围）
    print("\n[测试 6] 天气预报天数校验 (超出 1~7 范围)")
    resp = client.get(f"/api/v1/weather/forecast?city_code={test_city}&days=10")
    assert resp.status_code == 422, "超出范围应返回 422"
    body = resp.json()
    assert body["code"] == 1001, f"统一响应校验码应为 1001，实际: {body['code']}"
    print("  [PASS] 参数校验成功拦截非法预报天数")

    print("\n" + "=" * 60)
    print("  恭喜！天气模块全部 6 项测试用例全部 PASS！")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
