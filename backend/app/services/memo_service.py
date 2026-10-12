"""备忘录业务服务层 (MemoService)。

对应《接口契约》7.2。
遵循：
1. client_id 幂等防重放
2. version 乐观锁并发防覆盖
3. 软删除 deleted_at 控制
4. 置顶优先 + 更新时间降序排列
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
from app.models.sync import Memo
from app.schemas.memo import CreateMemoRequest, MemoItem, UpdateMemoRequest


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


class MemoService:
    """备忘录业务处理。"""

    def _to_item(self, memo: Memo) -> MemoItem:
        return MemoItem(
            id=memo.id,
            client_id=memo.client_id,
            title=memo.title,
            content=memo.content,
            is_pinned=memo.is_pinned,
            color=memo.color,
            version=memo.version,
            created_at=_to_iso(memo.created_at) or "",
            updated_at=_to_iso(memo.updated_at) or "",
        )

    def list_memos(
        self,
        db: Session,
        user_id: int,
        is_pinned: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageData[MemoItem]:
        """获取备忘录分页列表（置顶优先 + updated_at 倒序）。"""
        stmt = select(Memo).where(Memo.user_id == user_id, Memo.deleted_at.is_(None))
        if is_pinned is not None:
            stmt = stmt.where(Memo.is_pinned == is_pinned)

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(total_stmt) or 0

        # 置顶降序（True 在前），更新时间降序，ID 倒序
        stmt = stmt.order_by(Memo.is_pinned.desc(), Memo.updated_at.desc(), Memo.id.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size)
        rows = db.scalars(stmt).all()
        items = [self._to_item(m) for m in rows]

        return PageData.create(items=items, total=total, page=page, page_size=page_size)

    def create_memo(self, db: Session, user_id: int, req: CreateMemoRequest) -> MemoItem:
        """新增备忘录（client_id 幂等）。"""
        existing = db.scalar(
            select(Memo).where(Memo.user_id == user_id, Memo.client_id == req.client_id)
        )
        if existing:
            return self._to_item(existing)

        memo = Memo(
            client_id=req.client_id,
            user_id=user_id,
            title=req.title,
            content=req.content,
            is_pinned=req.is_pinned if req.is_pinned is not None else False,
            color=req.color,
            version=1,
        )
        db.add(memo)
        db.commit()
        db.refresh(memo)
        return self._to_item(memo)

    def update_memo(self, db: Session, user_id: int, memo_id: int, req: UpdateMemoRequest) -> MemoItem:
        """修改备忘录（乐观锁版本校验）。"""
        memo = db.scalar(
            select(Memo).where(Memo.id == memo_id, Memo.user_id == user_id, Memo.deleted_at.is_(None))
        )
        if not memo:
            raise BusinessException(ErrorCode.MEMO_NOT_FOUND)

        if memo.version != req.version:
            raise BusinessException(ErrorCode.SYNC_VERSION_CONFLICT)

        if req.title is not None:
            memo.title = req.title
        if req.content is not None:
            memo.content = req.content
        if req.is_pinned is not None:
            memo.is_pinned = req.is_pinned
        if req.color is not None:
            memo.color = req.color

        memo.version += 1
        memo.updated_at = _now_dt()
        db.commit()
        db.refresh(memo)
        return self._to_item(memo)

    def delete_memo(self, db: Session, user_id: int, memo_id: int, version: int) -> None:
        """软删除备忘录（乐观锁版本校验）。"""
        memo = db.scalar(
            select(Memo).where(Memo.id == memo_id, Memo.user_id == user_id, Memo.deleted_at.is_(None))
        )
        if not memo:
            raise BusinessException(ErrorCode.MEMO_NOT_FOUND)

        if memo.version != version:
            raise BusinessException(ErrorCode.SYNC_VERSION_CONFLICT)

        now = _now_dt()
        memo.deleted_at = now
        memo.version += 1
        memo.updated_at = now
        db.commit()


memo_service = MemoService()
