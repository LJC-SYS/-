"""备忘录 API 路由。

对应《接口契约》7.2。
包含备忘录列表、新增备忘录、修改备忘录、删除备忘录。
"""

from typing import Optional
from fastapi import APIRouter, Path, Query, Request

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse, PageData
from app.schemas.memo import CreateMemoRequest, MemoItem, UpdateMemoRequest
from app.services.memo_service import memo_service

router = APIRouter(prefix="/memos", tags=["备忘录"])


def _rid(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@router.get(
    "",
    summary="备忘录列表",
    description="获取当前用户的备忘录分页列表，置顶优先 + 更新时间倒序排列。",
    response_model=ApiResponse[PageData[MemoItem]],
)
def list_memos(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    is_pinned: Optional[bool] = Query(None, description="是否置顶筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
) -> ApiResponse:
    page_data = memo_service.list_memos(
        db=db,
        user_id=current_user.id,
        is_pinned=is_pinned,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.ok(data=page_data, request_id=_rid(request))


@router.post(
    "",
    summary="新增备忘录",
    description="新增备忘录。支持客户端 client_id 幂等，同 client_id 重复提交返回已有记录。",
    response_model=ApiResponse[MemoItem],
)
def create_memo(
    request: Request,
    payload: CreateMemoRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse:
    item = memo_service.create_memo(db=db, user_id=current_user.id, req=payload)
    return ApiResponse.ok(data=item, request_id=_rid(request))


@router.patch(
    "/{id}",
    summary="修改备忘录",
    description="更新备忘录。必须携带 version 进行乐观锁校验，版本冲突返回 1407。",
    response_model=ApiResponse[MemoItem],
)
def update_memo(
    request: Request,
    payload: UpdateMemoRequest,
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(..., description="备忘录 ID"),
) -> ApiResponse:
    item = memo_service.update_memo(
        db=db,
        user_id=current_user.id,
        memo_id=id,
        req=payload,
    )
    return ApiResponse.ok(data=item, request_id=_rid(request))


@router.delete(
    "/{id}",
    summary="删除备忘录",
    description="软删除备忘录。必须携带 version 进行乐观锁校验，版本冲突返回 1407。",
    response_model=ApiResponse[None],
)
def delete_memo(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(..., description="备忘录 ID"),
    version: int = Query(..., description="乐观锁版本号"),
) -> ApiResponse:
    memo_service.delete_memo(
        db=db,
        user_id=current_user.id,
        memo_id=id,
        version=version,
    )
    return ApiResponse.ok(data=None, request_id=_rid(request))
