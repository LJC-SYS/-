"""请求日志与 request_id 中间件。

职责：
1. 为每个请求生成 request_id 并写入 request.state，响应头回传 X-Request-Id。
2. 记录访问日志：方法、路径、状态码、耗时。
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.access")

# 无需记录访问日志的路径（探活、静态资源、文档）
SKIP_PATHS = {"/health", "/favicon.ico", "/openapi.json", "/docs", "/redoc"}


class RequestContextMiddleware(BaseHTTPMiddleware):
    """生成 request_id 并记录访问日志。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
        request.state.request_id = request_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # 异常交由全局异常处理器，这里只记录耗时
            cost = (time.perf_counter() - start) * 1000
            logger.exception(
                "method=%s path=%s cost=%.1fms request_id=%s status=EXCEPTION",
                request.method, request.url.path, cost, request_id,
            )
            raise

        cost = (time.perf_counter() - start) * 1000
        response.headers["X-Request-Id"] = request_id

        if request.url.path not in SKIP_PATHS:
            level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(
                level,
                "method=%s path=%s status=%s cost=%.1fms request_id=%s",
                request.method, request.url.path, response.status_code, cost, request_id,
            )

        return response
