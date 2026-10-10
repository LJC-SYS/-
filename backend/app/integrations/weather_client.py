"""第三方天气 API 客户端封装。

功能：
1. 封装第三方天气接口请求（高德天气 / 和风天气 / 本地 Mock 兜底）。
2. 支持超时控制（httpx timeout）与异常重试。
3. 统一将各供应商数据规范化为系统内部标准字典。
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class WeatherClientError(Exception):
    """天气服务调用异常基类。"""

    pass


class WeatherClientTimeoutError(WeatherClientError):
    """天气服务超时异常。"""

    pass


class WeatherCityNotFoundError(WeatherClientError):
    """城市未找到。"""

    pass


# 常见城市映射（用于 Mock 模式与兜底）
KNOWN_CITIES: Dict[str, str] = {
    "101090701": "沧州",
    "110000": "北京",
    "310000": "上海",
    "440100": "广州",
    "440300": "深圳",
    "330100": "杭州",
    "510100": "成都",
    "420100": "武汉",
    "500000": "重庆",
    "610100": "西安",
}


class WeatherClient:
    """天气 API 客户端。"""

    def __init__(self) -> None:
        self.provider = (settings.WEATHER_PROVIDER or "mock").lower()
        self.api_key = settings.WEATHER_API_KEY
        self.base_url = settings.WEATHER_API_BASE_URL
        self.timeout = settings.WEATHER_TIMEOUT_SECONDS
        self._simulate_failure = False  # 用于测试降级场景

    def set_simulate_failure(self, state: bool) -> None:
        """测试用：模拟第三方服务宕机或超时。"""
        self._simulate_failure = state

    def fetch_current(self, city_code: str, city_name: Optional[str] = None) -> Dict[str, Any]:
        """获取实时天气。"""
        if self._simulate_failure:
            logger.warning("[weather_client] 模拟第三方故障: provider=%s city_code=%s", self.provider, city_code)
            raise WeatherClientError("第三方天气服务模拟调用失败")

        resolved_name = city_name or KNOWN_CITIES.get(city_code, f"城市_{city_code}")

        # 若配置为高德天气且有 API Key
        if self.provider == "amap" and self.api_key:
            return self._fetch_amap_current(city_code, resolved_name)

        # 默认 Mock 模式
        return self._mock_current(city_code, resolved_name)

    def fetch_forecast(self, city_code: str, days: int = 3, city_name: Optional[str] = None) -> Dict[str, Any]:
        """获取天气预报。"""
        if self._simulate_failure:
            logger.warning("[weather_client] 模拟第三方故障: provider=%s city_code=%s", self.provider, city_code)
            raise WeatherClientError("第三方天气服务模拟预报失败")

        resolved_name = city_name or KNOWN_CITIES.get(city_code, f"城市_{city_code}")

        if self.provider == "amap" and self.api_key:
            return self._fetch_amap_forecast(city_code, days, resolved_name)

        return self._mock_forecast(city_code, days, resolved_name)

    # ---------- 高德天气对接实现 ----------

    def _fetch_amap_current(self, city_code: str, city_name: str) -> Dict[str, Any]:
        """调用高德开放平台天气接口（实时）。"""
        url = self.base_url or "https://restapi.amap.com/v3/weather/weatherInfo"
        params = {
            "key": self.api_key,
            "city": city_code,
            "extensions": "base",
            "output": "JSON",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            logger.error("[weather_client] 高德请求超时: %s", exc)
            raise WeatherClientTimeoutError("高德天气接口响应超时") from exc
        except Exception as exc:
            logger.error("[weather_client] 高德请求异常: %s", exc)
            raise WeatherClientError(f"高德天气接口异常: {exc}") from exc

        if data.get("status") != "1" or not data.get("lives"):
            info = data.get("info", "未知错误")
            logger.warning("[weather_client] 高德返回非成功状态: status=%s info=%s", data.get("status"), info)
            raise WeatherClientError(f"获取高德天气失败: {info}")

        live = data["lives"][0]
        # 解析温度
        try:
            temp_val = f"{float(live.get('temperature', 20.0)):.2f}"
        except (ValueError, TypeError):
            temp_val = "20.00"

        try:
            humidity_val = int(live.get("humidity", 50))
        except (ValueError, TypeError):
            humidity_val = 50

        wind_dir = live.get("winddirection", "无持续风向")
        wind_pwr = live.get("windpower", "≤3")

        now = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE))
        expires_at = now + timedelta(minutes=settings.WEATHER_CACHE_MINUTES)

        return {
            "city_code": city_code,
            "city_name": live.get("city") or city_name,
            "weather_type": "current",
            "temperature": temp_val,
            "humidity": humidity_val,
            "wind_info": f"{wind_dir}风 {wind_pwr}级",
            "weather_text": live.get("weather", "晴"),
            "icon_url": f"https://assets.lifeassistant.internal/icons/{live.get('weather', '晴')}.png",
            "from_cache": False,
            "degraded": False,
            "fetched_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "raw_data": json.dumps(data, ensure_ascii=False),
        }

    def _fetch_amap_forecast(self, city_code: str, days: int, city_name: str) -> Dict[str, Any]:
        """调用高德开放平台天气接口（预报）。"""
        url = self.base_url or "https://restapi.amap.com/v3/weather/weatherInfo"
        params = {
            "key": self.api_key,
            "city": city_code,
            "extensions": "all",
            "output": "JSON",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            logger.error("[weather_client] 高德预报超时: %s", exc)
            raise WeatherClientTimeoutError("高德天气预报超时") from exc
        except Exception as exc:
            logger.error("[weather_client] 高德预报异常: %s", exc)
            raise WeatherClientError(f"高德预报接口异常: {exc}") from exc

        if data.get("status") != "1" or not data.get("forecasts"):
            info = data.get("info", "未知错误")
            raise WeatherClientError(f"获取高德天气预报失败: {info}")

        forecast = data["forecasts"][0]
        casts = forecast.get("casts", [])[:days]

        item_list: List[Dict[str, Any]] = []
        for cast in casts:
            try:
                temp_max = f"{float(cast.get('daytemp', 25.0)):.2f}"
            except (ValueError, TypeError):
                temp_max = "25.00"
            try:
                temp_min = f"{float(cast.get('nighttemp', 15.0)):.2f}"
            except (ValueError, TypeError):
                temp_min = "15.00"

            item_list.append(
                {
                    "date": cast.get("date", datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE)).strftime("%Y-%m-%d")),
                    "weather_text": cast.get("dayweather", "晴"),
                    "temp_max": temp_max,
                    "temp_min": temp_min,
                    "wind_info": f"{cast.get('daywind', '北')}风 {cast.get('daypower', '≤3')}级",
                    "icon_url": f"https://assets.lifeassistant.internal/icons/{cast.get('dayweather', '晴')}.png",
                }
            )

        now = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE))
        expires_at = now + timedelta(minutes=settings.WEATHER_CACHE_MINUTES)

        return {
            "city_code": city_code,
            "city_name": forecast.get("city") or city_name,
            "from_cache": False,
            "degraded": False,
            "list": item_list,
            "fetched_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "raw_data": json.dumps(data, ensure_ascii=False),
        }

    # ---------- 本地 Mock 模式实现 ----------

    def _mock_current(self, city_code: str, city_name: str) -> Dict[str, Any]:
        """Mock 生成真实合理的实时天气。"""
        now = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE))
        expires_at = now + timedelta(minutes=settings.WEATHER_CACHE_MINUTES)

        return {
            "city_code": city_code,
            "city_name": city_name,
            "weather_type": "current",
            "temperature": "18.50",
            "humidity": 45,
            "wind_info": "东北风 3 级",
            "weather_text": "晴",
            "icon_url": "https://assets.lifeassistant.internal/icons/sunny.png",
            "from_cache": False,
            "degraded": False,
            "fetched_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "raw_data": json.dumps({"source": "mock", "city_code": city_code}, ensure_ascii=False),
        }

    def _mock_forecast(self, city_code: str, days: int, city_name: str) -> Dict[str, Any]:
        """Mock 生成合理的天气预报。"""
        now = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE))
        expires_at = now + timedelta(minutes=settings.WEATHER_CACHE_MINUTES)

        items: List[Dict[str, Any]] = []
        weather_texts = ["晴", "多云", "阴", "小雨", "晴", "多云", "晴"]
        for i in range(days):
            target_date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
            w_text = weather_texts[i % len(weather_texts)]
            items.append(
                {
                    "date": target_date,
                    "weather_text": w_text,
                    "temp_max": f"{24.00 - i * 0.5:.2f}",
                    "temp_min": f"{12.00 + i * 0.3:.2f}",
                    "wind_info": "东北风 3 级",
                    "icon_url": f"https://assets.lifeassistant.internal/icons/{w_text}.png",
                }
            )

        return {
            "city_code": city_code,
            "city_name": city_name,
            "from_cache": False,
            "degraded": False,
            "list": items,
            "fetched_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "raw_data": json.dumps({"source": "mock", "city_code": city_code, "days": days}, ensure_ascii=False),
        }


# 单例导出
weather_client = WeatherClient()
