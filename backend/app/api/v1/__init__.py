"""v1 路由汇总。"""

from fastapi import APIRouter

from app.api.v1 import auth, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)

# ---------- 成员 2 业务接口已全部实现并注册 ----------
from app.api.v1 import (
    accounting,
    badges,
    checkins,
    memos,
    points,
    sync,
    todos,
    weather,
)

api_router.include_router(weather.router)
api_router.include_router(checkins.router)
api_router.include_router(points.router)
api_router.include_router(badges.router)
api_router.include_router(todos.router)
api_router.include_router(memos.router)
api_router.include_router(accounting.router)
api_router.include_router(sync.router)

