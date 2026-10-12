"""天气模块 Schema。

严格对应《接口契约》第 6.11、6.12 节定义。
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class CurrentWeatherOut(BaseModel):
    """实时天气出参。"""

    city_code: str = Field(..., description="城市编码")
    city_name: str = Field(..., description="城市名称")
    weather_type: str = Field(default="current", description="天气类型")
    temperature: str = Field(..., description="温度字符串，如 18.50")
    humidity: Optional[int] = Field(default=None, description="湿度百分比")
    wind_info: Optional[str] = Field(default=None, description="风向风力说明")
    weather_text: str = Field(..., description="天气现象描述")
    icon_url: Optional[str] = Field(default=None, description="天气图标地址")
    from_cache: bool = Field(default=False, description="是否来自缓存")
    degraded: bool = Field(default=False, description="是否降级返回")
    fetched_at: str = Field(..., description="数据获取时间 ISO 8601")
    expires_at: str = Field(..., description="缓存失效时间 ISO 8601")


class ForecastItem(BaseModel):
    """预报单日天气项。"""

    date: str = Field(..., description="日期 YYYY-MM-DD")
    weather_text: str = Field(..., description="天气现象描述")
    temp_max: str = Field(..., description="最高温度")
    temp_min: str = Field(..., description="最低温度")
    wind_info: Optional[str] = Field(default=None, description="风向风力")
    icon_url: Optional[str] = Field(default=None, description="图标地址")


class WeatherForecastOut(BaseModel):
    """天气预报出参。"""

    city_code: str = Field(..., description="城市编码")
    city_name: str = Field(..., description="城市名称")
    from_cache: bool = Field(default=False, description="是否来自缓存")
    degraded: bool = Field(default=False, description="是否降级返回")
    list: List[ForecastItem] = Field(..., description="预报列表")
