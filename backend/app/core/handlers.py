"""全局异常处理器。

统一把以下异常转为 ApiResponse 结构：
- BusinessException    业务异常
- RequestValidationError  参数校验失败（FastAPI/Pydantic）
- HTTPException        FastAPI 原生 HTTP 异常（如 404）
- Exception            未捕获异常

对应《接口契约》第二章「统一响应规范」。
"""

import logging
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.errors import ErrorCode, get_message
from app.core.exceptions import BusinessException
from app.core.response import ApiResponse

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    """取本次请求 ID，未生成则生成一个。"""
    rid = getattr(request.state, "request_id", None)
    if not rid:
        rid = uuid.uuid4().hex[:12]
        request.state.request_id = rid
    return rid


def _json(code: int, message: str, http_status: int, request: Request, data=None) -> JSONResponse:
    payload = ApiResponse.fail(code, message, data, _request_id(request))
    return JSONResponse(status_code=http_status, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """注册全部全局异常处理器。"""

    @app.exception_handler(BusinessException)
    async def _business_exception_handler(request: Request, exc: BusinessException):
        # 业务异常属于预期内，按 info 记录，便于排查但不污染错误日志
        logger.info(
            "[business] code=%s path=%s detail=%s request_id=%s",
            exc.code, request.url.path, exc.message, _request_id(request),
        )
        return _json(exc.code, exc.message, exc.http_status, request, exc.data)

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(request: Request, exc: RequestValidationError):
        # 提取首个校验错误，给出可读提示
        errors = exc.errors()
        first = errors[0] if errors else {}
        loc = ".".join(str(x) for x in first.get("loc", []) if x not in ("body", "query", "path"))
        msg = first.get("msg", "参数校验失败")
        human = f"参数校验失败：{loc} {msg}".strip() if loc else "参数校验失败"

        logger.info(
            "[validation] path=%s errors=%s request_id=%s",
            request.url.path, errors, _request_id(request),
        )

        # 开发环境附带详细错误，便于联调定位。
        # 注意：pydantic 的 ctx 里可能含 ValueError 等不可 JSON 序列化对象，需转成字符串。
        extra = None
        if settings.is_local:
            extra = [
                {
                    "loc": [str(x) for x in e.get("loc", [])],
                    "msg": str(e.get("msg", "")),
                    "type": str(e.get("type", "")),
                }
                for e in errors
            ]

        return _json(ErrorCode.PARAM_INVALID, human, status.HTTP_422_UNPROCESSABLE_ENTITY, request, extra)

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return _json(ErrorCode.NOT_FOUND, "接口路径不存在", 404, request)
        if exc.status_code == status.HTTP_403_FORBIDDEN:
            return _json(ErrorCode.FORBIDDEN, get_message(ErrorCode.FORBIDDEN), 403, request)
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return _json(ErrorCode.UNAUTHORIZED, get_message(ErrorCode.UNAUTHORIZED), 401, request)
        return _json(
            int(exc.status_code) * 100 if exc.status_code < 100 else exc.status_code,
            str(exc.detail),
            exc.status_code,
            request,
        )

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        rid = _request_id(request)
        logger.exception(
            "[unhandled] path=%s request_id=%s error=%s",
            request.url.path, rid, exc,
        )
        # 正式环境隐藏堆栈，仅返回 request_id 供排查
        data = None
        if settings.is_local:
            data = {"error_type": type(exc).__name__, "error_detail": str(exc)}
        return _json(
            ErrorCode.INTERNAL_ERROR,
            get_message(ErrorCode.INTERNAL_ERROR),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            request,
            data,
        )
