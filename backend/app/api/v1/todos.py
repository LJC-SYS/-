"""待办事项 API 路由。

对应《接口契约》7.1。
包含待办列表、新增待办、修改待办、删除待办。
"""

from typing import Optional
from fastapi import APIRouter, Path, Query, Request

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse, PageData
from app.schemas.todo import CreateTodoRequest, TodoItem, UpdateTodoRequest
from app.services.todo_service import todo_service

router = APIRouter(prefix="/todos", tags=["待办事项"])


def _rid(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@router.get(
    "",
    summary="待办列表",
    description="获取当前用户的待办事项分页列表，支持按状态与优先级筛选。",
    response_model=ApiResponse[PageData[TodoItem]],
)
def list_todos(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    status: Optional[str] = Query(None, description="状态: pending/completed/cancelled"),
    priority: Optional[str] = Query(None, description="优先级: low/normal/high"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
) -> ApiResponse:
    page_data = todo_service.list_todos(
        db=db,
        user_id=current_user.id,
        status=status,
        priority=priority,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.ok(data=page_data, request_id=_rid(request))


@router.post(
    "",
    summary="新增待办",
    description="新增待办事项。支持客户端 client_id 幂等，同 client_id 重复提交返回已有记录。",
    response_model=ApiResponse[TodoItem],
)
def create_todo(
    request: Request,
    payload: CreateTodoRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse:
    item = todo_service.create_todo(db=db, user_id=current_user.id, req=payload)
    return ApiResponse.ok(data=item, request_id=_rid(request))


@router.patch(
    "/{id}",
    summary="修改待办",
    description="更新待办事项。必须携带 version 进行乐观锁校验，版本冲突返回 1407。",
    response_model=ApiResponse[TodoItem],
)
def update_todo(
    request: Request,
    payload: UpdateTodoRequest,
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(..., description="待办 ID"),
) -> ApiResponse:
    item = todo_service.update_todo(
        db=db,
        user_id=current_user.id,
        todo_id=id,
        req=payload,
    )
    return ApiResponse.ok(data=item, request_id=_rid(request))


@router.delete(
    "/{id}",
    summary="删除待办",
    description="软删除待办事项。必须携带 version 进行乐观锁校验，版本冲突返回 1407。",
    response_model=ApiResponse[None],
)
def delete_todo(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(..., description="待办 ID"),
    version: int = Query(..., description="乐观锁版本号"),
) -> ApiResponse:
    todo_service.delete_todo(
        db=db,
        user_id=current_user.id,
        todo_id=id,
        version=version,
    )
    return ApiResponse.ok(data=None, request_id=_rid(request))
