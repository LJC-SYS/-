"""天气业务服务层。

实现规则：
1. 优先读取 WeatherCache 缓存（有效期通常为 30 分钟）。
2. 缓存失效或不存在时调用天气第三方 Client 并回写缓存。
3. 优雅降级铁律（必须遵守）：
   - 第三方不可用/超时且有缓存时（无论缓存是否过期），返回缓存并标记：
     from_cache=True, degraded=True, HTTP 200, code=0。绝不返回 500！
   - 第三方不可用且完全无缓存时，抛出 BusinessException(ErrorCode.WEATHER_NO_CACHE)。
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ErrorCode
from app.core.exceptions import BusinessException
from app.integrations.weather_client import WeatherClientError, weather_client
from app.models.sync import WeatherCache

logger = logging.getLogger(__name__)


def _is_cache_valid(expires_at: Optional[datetime], now: datetime) -> bool:
    if not expires_at:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=ZoneInfo(settings.BUSINESS_TIMEZONE))
    return expires_at > now


class WeatherService:
    """天气服务。"""

    def get_current_weather(
        self, db: Session, city_code: str, city_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取实时天气（支持缓存与优雅降级）。"""
        now = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE))

        cache: Optional[WeatherCache] = db.execute(
            select(WeatherCache).where(
                WeatherCache.location_code == city_code,
                WeatherCache.weather_type == "current",
            )
        ).scalar_one_or_none()

        # 1. 命中未过期缓存，直接返回
        if cache and _is_cache_valid(cache.expires_at, now):
            logger.info("[weather_service] 命中有效缓存: city_code=%s", city_code)
            return self._build_current_from_cache(cache, city_name, degraded=False)

        # 2. 缓存失效或无缓存，尝试请求第三方
        try:
            live_data = weather_client.fetch_current(city_code=city_code, city_name=city_name)
            self._save_current_cache(db, cache, live_data)
            return {
                "city_code": live_data["city_code"],
                "city_name": live_data["city_name"],
                "weather_type": "current",
                "temperature": live_data["temperature"],
                "humidity": live_data["humidity"],
                "wind_info": live_data["wind_info"],
                "weather_text": live_data["weather_text"],
                "icon_url": live_data.get("icon_url"),
                "from_cache": False,
                "degraded": False,
                "fetched_at": live_data["fetched_at"],
                "expires_at": live_data["expires_at"],
            }
        except (WeatherClientError, Exception) as exc:
            logger.warning("[weather_service] 第三方天气获取失败: city_code=%s, error=%s", city_code, exc)

            # 3. 降级：存在历史缓存（即使已过期）
            if cache:
                logger.info("[weather_service] 触发降级，返回旧缓存数据: city_code=%s", city_code)
                return self._build_current_from_cache(cache, city_name, degraded=True)

            # 4. 既失败又无历史缓存
            raise BusinessException(
                code=ErrorCode.WEATHER_NO_CACHE,
                message="暂无天气数据，请稍后重试",
            ) from exc

    def get_forecast_weather(
        self, db: Session, city_code: str, days: int = 3, city_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取天气预报（支持缓存与优雅降级）。"""
        now = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE))

        cache: Optional[WeatherCache] = db.execute(
            select(WeatherCache).where(
                WeatherCache.location_code == city_code,
                WeatherCache.weather_type == "forecast",
            )
        ).scalar_one_or_none()

        # 1. 命中未过期缓存
        if cache and _is_cache_valid(cache.expires_at, now):
            logger.info("[weather_service] 命中有效预报缓存: city_code=%s", city_code)
            return self._build_forecast_from_cache(cache, days, city_name, degraded=False)

        # 2. 缓存失效或无缓存，尝试请求第三方
        try:
            live_forecast = weather_client.fetch_forecast(city_code=city_code, days=days, city_name=city_name)
            self._save_forecast_cache(db, cache, live_forecast)
            return {
                "city_code": live_forecast["city_code"],
                "city_name": live_forecast["city_name"],
                "from_cache": False,
                "degraded": False,
                "list": live_forecast["list"][:days],
            }
        except (WeatherClientError, Exception) as exc:
            logger.warning("[weather_service] 第三方预报获取失败: city_code=%s, error=%s", city_code, exc)

            # 3. 降级：存在历史缓存
            if cache:
                logger.info("[weather_service] 触发预报降级，返回旧缓存数据: city_code=%s", city_code)
                return self._build_forecast_from_cache(cache, days, city_name, degraded=True)

            # 4. 既失败又无缓存
            raise BusinessException(
                code=ErrorCode.WEATHER_NO_CACHE,
                message="暂无天气数据，请稍后重试",
            ) from exc

    # ---------- 内部辅助方法 ----------

    def _build_current_from_cache(
        self, cache: WeatherCache, fallback_name: Optional[str], degraded: bool
    ) -> Dict[str, Any]:
        """从缓存对象组装实时天气出参。"""
        raw: Dict[str, Any] = {}
        if cache.raw_data:
            try:
                raw = json.loads(cache.raw_data)
            except Exception:
                raw = {}

        weather_text = raw.get("weather_text") or "晴"
        icon_url = raw.get("icon_url") or f"https://assets.lifeassistant.internal/icons/{weather_text}.png"

        temp_str = f"{cache.temperature:.2f}" if cache.temperature is not None else "20.00"

        return {
            "city_code": cache.location_code,
            "city_name": cache.location_name or fallback_name or cache.location_code,
            "weather_type": "current",
            "temperature": temp_str,
            "humidity": cache.humidity,
            "wind_info": cache.wind_info,
            "weather_text": weather_text,
            "icon_url": icon_url,
            "from_cache": True,
            "degraded": degraded,
            "fetched_at": cache.fetched_at.isoformat() if cache.fetched_at else "",
            "expires_at": cache.expires_at.isoformat() if cache.expires_at else "",
        }

    def _build_forecast_from_cache(
        self, cache: WeatherCache, days: int, fallback_name: Optional[str], degraded: bool
    ) -> Dict[str, Any]:
        """从缓存对象组装预报出参。"""
        items = []
        if cache.raw_data:
            try:
                raw = json.loads(cache.raw_data)
                items = raw.get("list", [])
            except Exception:
                items = []

        return {
            "city_code": cache.location_code,
            "city_name": cache.location_name or fallback_name or cache.location_code,
            "from_cache": True,
            "degraded": degraded,
            "list": items[:days],
        }

    def _save_current_cache(
        self, db: Session, cache: Optional[WeatherCache], data: Dict[str, Any]
    ) -> None:
        """保存实时天气缓存。"""
        fetched_at = datetime.fromisoformat(data["fetched_at"])
        expires_at = datetime.fromisoformat(data["expires_at"])
        temp_dec = Decimal(data["temperature"]) if data.get("temperature") else None

        # 将展示字段并入 raw_data 方便直接还原
        raw_dict = {
            "weather_text": data.get("weather_text", "晴"),
            "icon_url": data.get("icon_url"),
            "source_raw": data.get("raw_data"),
        }

        if cache:
            cache.location_name = data["city_name"]
            cache.temperature = temp_dec
            cache.humidity = data.get("humidity")
            cache.wind_info = data.get("wind_info")
            cache.raw_data = json.dumps(raw_dict, ensure_ascii=False)
            cache.fetched_at = fetched_at
            cache.expires_at = expires_at
        else:
            cache = WeatherCache(
                provider=settings.WEATHER_PROVIDER or "mock",
                location_code=data["city_code"],
                location_name=data["city_name"],
                weather_type="current",
                temperature=temp_dec,
                humidity=data.get("humidity"),
                wind_info=data.get("wind_info"),
                raw_data=json.dumps(raw_dict, ensure_ascii=False),
                fetched_at=fetched_at,
                expires_at=expires_at,
            )
            db.add(cache)

        db.commit()

    def _save_forecast_cache(
        self, db: Session, cache: Optional[WeatherCache], data: Dict[str, Any]
    ) -> None:
        """保存天气预报缓存。"""
        fetched_at = datetime.fromisoformat(data["fetched_at"])
        expires_at = datetime.fromisoformat(data["expires_at"])

        raw_dict = {
            "list": data.get("list", []),
            "source_raw": data.get("raw_data"),
        }

        if cache:
            cache.location_name = data["city_name"]
            cache.raw_data = json.dumps(raw_dict, ensure_ascii=False)
            cache.fetched_at = fetched_at
            cache.expires_at = expires_at
        else:
            cache = WeatherCache(
                provider=settings.WEATHER_PROVIDER or "mock",
                location_code=data["city_code"],
                location_name=data["city_name"],
                weather_type="forecast",
                raw_data=json.dumps(raw_dict, ensure_ascii=False),
                fetched_at=fetched_at,
                expires_at=expires_at,
            )
            db.add(cache)

        db.commit()


# 单例导出
weather_service = WeatherService()
