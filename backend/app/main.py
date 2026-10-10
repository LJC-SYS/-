"""应用入口。

启动方式：
    python -m app.main
或：
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.errors import ErrorCode
from app.core.handlers import register_exception_handlers
from app.core.logging_conf import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.core.response import ApiResponse

setup_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """构建 FastAPI 应用。"""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "一站式综合生活助手后端接口。\n\n"
            "**统一响应规范**：所有接口返回 `{code, message, data, request_id, timestamp}`，"
            "客户端只需判断 `code == 0`。\n\n"
            "业务错误码见项目 `docs/接口契约.md` 第三章。"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # 中间件（后添加的先执行，注意顺序：CORS 最外层）
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    register_exception_handlers(application)

    # 健康检查
    @application.get("/health", tags=["系统"], summary="健康检查")
    def health():
        db_status = "connected"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:  # pragma: no cover
            logger.warning("[health] database check failed: %s", exc)
            db_status = "disconnected"

        return ApiResponse.ok(
            {
                "status": "ok",
                "version": settings.APP_VERSION,
                "env": settings.APP_ENV,
                "database": db_status,
            }
        )

    application.include_router(api_router)

    @application.on_event("startup")
    def _on_startup():
        logger.info(
            "应用启动 env=%s version=%s cors=%s",
            settings.APP_ENV, settings.APP_VERSION, settings.cors_origins_list,
        )

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.is_local,
    )
