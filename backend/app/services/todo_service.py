"""待办事项业务服务层 (TodoService)。

对应《接口契约》7.1。
遵循：
1. client_id 幂等防重放
2. version 乐观锁并发防覆盖
3. 软删除 deleted_at 控制
"""

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ErrorCode
from app.core.exceptions import BusinessException
from app.core.response import PageData
from app.models.sync import Todo
from app.schemas.todo import CreateTodoRequest, TodoItem, UpdateTodoRequest


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(settings.BUSINESS_TIMEZONE))
    else:
        dt = dt.astimezone(ZoneInfo(settings.BUSINESS_TIMEZONE))
    return dt.isoformat()


class TodoService:
    """待办事项业务处理。"""

    def _to_item(self, todo: Todo) -> TodoItem:
        return TodoItem(
            id=todo.id,
            client_id=todo.client_id,
            title=todo.title,
            description=todo.description,
            priority=todo.priority,
            status=todo.status,
            due_at=_to_iso(todo.due_at),
            completed_at=_to_iso(todo.completed_at),
            sort_order=todo.sort_order,
            version=todo.version,
            created_at=_to_iso(todo.created_at) or "",
            updated_at=_to_iso(todo.updated_at) or "",
        )

    def list_todos(
        self,
        db: Session,
        user_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageData[TodoItem]:
        """获取待办事项分页列表。"""
        stmt = select(Todo).where(Todo.user_id == user_id, Todo.deleted_at.is_(None))
        if status:
            stmt = stmt.where(Todo.status == status)
        if priority:
            stmt = stmt.where(Todo.priority == priority)

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(total_stmt) or 0

        # 按自定义排序值升序、ID 倒序排列
        stmt = stmt.order_by(Todo.sort_order.asc(), Todo.id.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = db.scalars(stmt).all()
        items = [self._to_item(t) for t in rows]

        return PageData.create(items=items, total=total, page=page, page_size=page_size)

    def create_todo(self, db: Session, user_id: int, req: CreateTodoRequest) -> TodoItem:
        """新增待办事项（client_id 幂等）。"""
        # 幂等检查：同 user_id + client_id 重复提交返回已有记录，不报错、不重复插入
        existing = db.scalar(
            select(Todo).where(Todo.user_id == user_id, Todo.client_id == req.client_id)
        )
        if existing:
            return self._to_item(existing)

        todo = Todo(
            client_id=req.client_id,
            user_id=user_id,
            title=req.title,
            description=req.description,
            priority=req.priority or "normal",
            status="pending",
            due_at=req.due_at,
            sort_order=req.sort_order or 0,
            version=1,
        )
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return self._to_item(todo)

    def update_todo(self, db: Session, user_id: int, todo_id: int, req: UpdateTodoRequest) -> TodoItem:
        """修改待办事项（乐观锁版本校验）。"""
        todo = db.scalar(
            select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id, Todo.deleted_at.is_(None))
        )
        if not todo:
            raise BusinessException(ErrorCode.TODO_NOT_FOUND)

        if todo.version != req.version:
            raise BusinessException(ErrorCode.SYNC_VERSION_CONFLICT)

        if req.title is not None:
            todo.title = req.title
        if req.description is not None:
            todo.description = req.description
        if req.priority is not None:
            todo.priority = req.priority
        if req.due_at is not None:
            todo.due_at = req.due_at
        if req.sort_order is not None:
            todo.sort_order = req.sort_order

        if req.status is not None:
            if req.status == "completed" and todo.status != "completed":
                todo.completed_at = _now_dt()
            elif req.status in ("pending", "cancelled"):
                todo.completed_at = None
            todo.status = req.status

        todo.version += 1
        todo.updated_at = _now_dt()
        db.commit()
        db.refresh(todo)
        return self._to_item(todo)

    def delete_todo(self, db: Session, user_id: int, todo_id: int, version: int) -> None:
        """软删除待办事项（乐观锁版本校验）。"""
        todo = db.scalar(
            select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id, Todo.deleted_at.is_(None))
        )
        if not todo:
            raise BusinessException(ErrorCode.TODO_NOT_FOUND)

        if todo.version != version:
            raise BusinessException(ErrorCode.SYNC_VERSION_CONFLICT)

        now = _now_dt()
        todo.deleted_at = now
        todo.version += 1
        todo.updated_at = now
        db.commit()


todo_service = TodoService()
