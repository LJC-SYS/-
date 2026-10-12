"""徽章路由。

对应《接口契约》6.18（徽章列表）。
属于成员 2 核心职责模块。
"""

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse
from app.schemas.checkin import BadgeListResponseData
from app.services.checkin_service import checkin_service

router = APIRouter(prefix="/badges", tags=["徽章"])


def _rid(request: Request) -> str:
    """提取统一请求 ID。"""
    return getattr(request.state, "request_id", "")


@router.get(
    "",
    summary="徽章列表",
    description=(
        "获取系统全量徽章及当前用户解锁状态。\n\n"
        "- 每项徽章包含 earned (true/false) 与 earned_at 字段，方便客户端灰色/彩色渲染。\n"
        "- 返回 earned_count 与 total_count。"
    ),
    response_model=ApiResponse[BadgeListResponseData],
)
def get_badges_list(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse:
    """获取徽章列表。"""
    data = checkin_service.get_badges(db=db, user=current_user)
    return ApiResponse.ok(data, request_id=_rid(request))
