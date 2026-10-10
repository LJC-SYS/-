"""统一响应体与分页结构。

所有接口（成功与业务失败）都返回 ApiResponse 结构，客户端只判断 code。
详见《接口契约》第二章。
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.errors import ErrorCode, get_message

T = TypeVar("T")


def _now_iso() -> str:
    """返回业务时区当前时间 ISO 8601 字符串。"""
    tz = timezone(timedelta(hours=8))
    try:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo(settings.BUSINESS_TIMEZONE)
    except Exception:  # pragma: no cover - 时区库缺失时降级为 UTC+8
        pass
    return datetime.now(tz).isoformat()


class ApiResponse(BaseModel, Generic[T]):
    """统一响应体。"""

    code: int = Field(default=0, description="0 表示成功，非 0 为业务错误码")
    message: str = Field(default="success", description="提示信息")
    data: Optional[T] = Field(default=None, description="业务数据")
    request_id: str = Field(default="", description="请求唯一标识")
    timestamp: str = Field(default_factory=_now_iso, description="服务器时间 ISO 8601")

    @classmethod
    def ok(cls, data: Any = None, message: str = "success", request_id: str = "") -> "ApiResponse":
        return cls(code=0, message=message, data=data, request_id=request_id)

    @classmethod
    def fail(cls, code: int, message: Optional[str] = None, data: Any = None, request_id: str = "") -> "ApiResponse":
        return cls(
            code=int(code),
            message=get_message(int(code), message or ""),
            data=data,
            request_id=request_id,
        )


class PageData(BaseModel, Generic[T]):
    """分页数据结构。"""

    list: List[T] = Field(default_factory=list, description="当前页数据")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页条数")
    total: int = Field(default=0, description="总条数")
    total_pages: int = Field(default=0, description="总页数")

    @classmethod
    def create(cls, items: List[Any], page: int, page_size: int, total: int) -> "PageData":
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            list=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )


class PageQuery(BaseModel):
    """分页请求参数基类，各列表接口直接继承。"""

    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，1~100")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def success(data: Any = None, request_id: str = "") -> dict:
    """快捷构造成功响应（供需要直接返回 dict 的场景使用）。"""
    return ApiResponse.ok(data=data, request_id=request_id).model_dump()
