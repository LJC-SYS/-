"""云端增量同步 API 路由。

对应《接口契约》第八章。
包含推送本地变更 (/sync/push) 与拉取增量 (/sync/pull)。
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, Request

from app.api.deps import CurrentUser, DbSession
from app.core.errors import ErrorCode
from app.core.exceptions import BusinessException
from app.core.response import ApiResponse
from app.schemas.sync import (
    SyncPullResponseData,
    SyncPushRequest,
    SyncPushResponseData,
)
from app.services.sync_service import sync_service

router = APIRouter(prefix="/sync", tags=["数据同步"])


def _rid(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@router.post(
    "/push",
    summary="推送本地变更",
    description=(
        "客户端批量推送本地离线生成的变更（增/改/删）。\n\n"
        "- 实体范围: todo, memo, accounting\n"
        "- 服务端优先 (Last-Write-Wins by server) 解决并发冲突\n"
        "- 单项冲突返回 status=conflict 并附带 server_data，不阻塞批次中其他项"
    ),
    response_model=ApiResponse[SyncPushResponseData],
)
def push_changes(
    request: Request,
    payload: SyncPushRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse:
    data = sync_service.push(
        db=db,
        user_id=current_user.id,
        req=payload,
    )
    return ApiResponse.ok(data=data, request_id=_rid(request))


@router.get(
    "/pull",
    summary="拉取增量",
    description=(
        "按时间戳增量拉取自 since 之后的云端更新与软删除记录。\n\n"
        "- 支持 entity_types 过滤（逗号分隔）\n"
        "- 支持 limit 分页与 has_more 状态指示"
    ),
    response_model=ApiResponse[SyncPullResponseData],
)
def pull_changes(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    since: str = Query(..., description="上次同步时间 ISO 8601，首次传 1970-01-01T00:00:00+08:00"),
    entity_types: Optional[str] = Query(None, description="逗号分隔，如 todo,memo,accounting"),
    limit: int = Query(200, ge=1, le=500, description="单次拉取上限"),
) -> ApiResponse:
    clean_since = since.strip()
    if " " in clean_since and "+" not in clean_since:
        clean_since = clean_since.replace(" ", "+")
    try:
        since_dt = datetime.fromisoformat(clean_since)
    except Exception:
        raise BusinessException(ErrorCode.PARAM_INVALID, message="since 格式不正确，需符合 ISO 8601")

    data = sync_service.pull(
        db=db,
        user_id=current_user.id,
        since=since_dt,
        entity_types=entity_types,
        limit=limit,
    )
    return ApiResponse.ok(data=data, request_id=_rid(request))
