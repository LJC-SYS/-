"""天气路由：生活工具接口。

对应《接口契约》6.11（当前天气）与 6.12（天气预报）。
属于成员 2 核心职责模块。
"""

from typing import Optional

from fastapi import APIRouter, Query, Request

from app.api.deps import DbSession
from app.core.response import ApiResponse
from app.schemas.weather import CurrentWeatherOut, WeatherForecastOut
from app.services.weather_service import weather_service

router = APIRouter(prefix="/weather", tags=["生活工具 - 天气"])


def _rid(request: Request) -> str:
    """提取统一请求 ID。"""
    return getattr(request.state, "request_id", "")


@router.get(
    "/current",
    summary="当前天气",
    description=(
        "获取指定城市的实时天气数据。\n\n"
        "- 优先走本地缓存（默认 30 分钟）。\n"
        "- 若第三方服务异常但本地有历史缓存，自动触发降级返回并标明 degraded=True。\n"
        "- 无需鉴权。"
    ),
    response_model=ApiResponse[CurrentWeatherOut],
)
def get_current_weather(
    request: Request,
    db: DbSession,
    city_code: str = Query(..., description="城市编码，如沧州: 101090701"),
    city_name: Optional[str] = Query(default=None, description="城市名称（可选），如沧州"),
) -> ApiResponse:
    """获取实时天气。"""
    data = weather_service.get_current_weather(db=db, city_code=city_code, city_name=city_name)
    return ApiResponse.ok(data, request_id=_rid(request))


@router.get(
    "/forecast",
    summary="天气预报",
    description=(
        "获取未来 1~7 天天气预报。\n\n"
        "- 默认获取 3 天预报。\n"
        "- 具备缓存与降级机制。\n"
        "- 无需鉴权。"
    ),
    response_model=ApiResponse[WeatherForecastOut],
)
def get_weather_forecast(
    request: Request,
    db: DbSession,
    city_code: str = Query(..., description="城市编码，如沧州: 101090701"),
    days: int = Query(default=3, ge=1, le=7, description="预报天数（1~7 天，默认 3）"),
    city_name: Optional[str] = Query(default=None, description="城市名称（可选）"),
) -> ApiResponse:
    """获取天气预报。"""
    data = weather_service.get_forecast_weather(db=db, city_code=city_code, days=days, city_name=city_name)
    return ApiResponse.ok(data, request_id=_rid(request))
