"""云端增量双向同步服务层 (SyncService)。

对应《接口契约》第八章与《数据库表设计》第六章。
核心机制：
1. 双向增量同步：推送变更 (push) 与拉取增量 (pull)
2. 实体范围：todos, memos, accounting_records
3. 冲突解决策略：服务端优先 (Last-Write-Wins by server)
4. client_id 幂等防重放 + version 乐观锁
5. 软删除联动：deleted_at 识别与客户端本地删除通知
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.sync import AccountingCategory, AccountingRecord, Memo, Todo
from app.schemas.sync import (
    SyncPullChangeItem,
    SyncPullResponseData,
    SyncPushChangeItem,
    SyncPushRequest,
    SyncPushResponseData,
    SyncPushResultItem,
)


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


def _format_amount(val: Optional[Decimal]) -> str:
    if val is None:
        return "0.00"
    return f"{val:.2f}"


def _normalize_dt(dt: datetime) -> datetime:
    """消除时区以便与 SQLite 存储的 naive UTC 时间比较。"""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class SyncService:
    """增量同步核心业务。"""

    def push(self, db: Session, user_id: int, req: SyncPushRequest) -> SyncPushResponseData:
        """批量推送本地变更。"""
        results: List[SyncPushResultItem] = []
        has_conflict = False

        for change in req.changes:
            res = self._process_single_change(db, user_id, change)
            results.append(res)
            if res.status == "conflict":
                has_conflict = True

        db.commit()

        return SyncPushResponseData(
            results=results,
            partial_failure=has_conflict,
            server_time=_to_iso(_now_dt()) or "",
        )

    def _process_single_change(
        self, db: Session, user_id: int, change: SyncPushChangeItem
    ) -> SyncPushResultItem:
        """处理单项变更。"""
        etype = change.entity_type
        if etype == "todo":
            return self._sync_todo(db, user_id, change)
        elif etype == "memo":
            return self._sync_memo(db, user_id, change)
        elif etype == "accounting":
            return self._sync_accounting(db, user_id, change)
        else:
            return SyncPushResultItem(
                client_id=change.client_id,
                entity_type=etype,
                status="skipped",
            )

    def _sync_todo(self, db: Session, user_id: int, change: SyncPushChangeItem) -> SyncPushResultItem:
        todo = db.scalar(
            select(Todo).where(Todo.user_id == user_id, Todo.client_id == change.client_id)
        )
        data = change.data or {}

        if change.action == "create":
            if todo:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="todo",
                    status="skipped",
                    server_id=todo.id,
                    version=todo.version,
                )
            due_at = None
            if data.get("due_at"):
                try:
                    due_at = datetime.fromisoformat(data["due_at"])
                except Exception:
                    pass

            new_todo = Todo(
                client_id=change.client_id,
                user_id=user_id,
                title=data.get("title") or "未命名待办",
                description=data.get("description"),
                priority=data.get("priority") or "normal",
                status=data.get("status") or "pending",
                due_at=due_at,
                sort_order=data.get("sort_order") or 0,
                version=1,
            )
            db.add(new_todo)
            db.flush()
            return SyncPushResultItem(
                client_id=change.client_id,
                entity_type="todo",
                status="created",
                server_id=new_todo.id,
                version=1,
            )

        elif change.action == "update":
            if not todo or todo.deleted_at is not None:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="todo",
                    status="conflict",
                    server_id=todo.id if todo else None,
                    server_version=todo.version if todo else 0,
                    server_data=None,
                )
            if todo.version != change.version:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="todo",
                    status="conflict",
                    server_id=todo.id,
                    server_version=todo.version,
                    server_data={
                        "title": todo.title,
                        "description": todo.description,
                        "priority": todo.priority,
                        "status": todo.status,
                        "due_at": _to_iso(todo.due_at),
                        "sort_order": todo.sort_order,
                    },
                )
            # 正常更新
            if "title" in data and data["title"] is not None:
                todo.title = data["title"]
            if "description" in data:
                todo.description = data["description"]
            if "priority" in data and data["priority"] is not None:
                todo.priority = data["priority"]
            if "status" in data and data["status"] is not None:
                if data["status"] == "completed" and todo.status != "completed":
                    todo.completed_at = _now_dt()
                elif data["status"] in ("pending", "cancelled"):
                    todo.completed_at = None
                todo.status = data["status"]
            if "due_at" in data:
                try:
                    todo.due_at = datetime.fromisoformat(data["due_at"]) if data["due_at"] else None
                except Exception:
                    pass
            if "sort_order" in data and data["sort_order"] is not None:
                todo.sort_order = data["sort_order"]

            todo.version += 1
            todo.updated_at = _now_dt()
            db.flush()
            return SyncPushResultItem(
                client_id=change.client_id,
                entity_type="todo",
                status="updated",
                server_id=todo.id,
                version=todo.version,
            )

        elif change.action == "delete":
            if not todo or todo.deleted_at is not None:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="todo",
                    status="skipped",
                    server_id=todo.id if todo else None,
                    version=todo.version if todo else None,
                )
            if todo.version != change.version:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="todo",
                    status="conflict",
                    server_id=todo.id,
                    server_version=todo.version,
                    server_data={"title": todo.title},
                )
            now = _now_dt()
            todo.deleted_at = now
            todo.version += 1
            todo.updated_at = now
            db.flush()
            return SyncPushResultItem(
                client_id=change.client_id,
                entity_type="todo",
                status="deleted",
                server_id=todo.id,
                version=todo.version,
            )

        return SyncPushResultItem(client_id=change.client_id, entity_type="todo", status="skipped")

    def _sync_memo(self, db: Session, user_id: int, change: SyncPushChangeItem) -> SyncPushResultItem:
        memo = db.scalar(
            select(Memo).where(Memo.user_id == user_id, Memo.client_id == change.client_id)
        )
        data = change.data or {}

        if change.action == "create":
            if memo:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="memo",
                    status="skipped",
                    server_id=memo.id,
                    version=memo.version,
                )
            new_memo = Memo(
                client_id=change.client_id,
                user_id=user_id,
                title=data.get("title"),
                content=data.get("content") or "",
                is_pinned=bool(data.get("is_pinned", False)),
                color=data.get("color"),
                version=1,
            )
            db.add(new_memo)
            db.flush()
            return SyncPushResultItem(
                client_id=change.client_id,
                entity_type="memo",
                status="created",
                server_id=new_memo.id,
                version=1,
            )

        elif change.action == "update":
            if not memo or memo.deleted_at is not None:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="memo",
                    status="conflict",
                    server_id=memo.id if memo else None,
                    server_version=memo.version if memo else 0,
                    server_data=None,
                )
            if memo.version != change.version:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="memo",
                    status="conflict",
                    server_id=memo.id,
                    server_version=memo.version,
                    server_data={
                        "title": memo.title,
                        "content": memo.content,
                        "is_pinned": memo.is_pinned,
                        "color": memo.color,
                    },
                )
            if "title" in data:
                memo.title = data["title"]
            if "content" in data and data["content"] is not None:
                memo.content = data["content"]
            if "is_pinned" in data and data["is_pinned"] is not None:
                memo.is_pinned = data["is_pinned"]
            if "color" in data:
                memo.color = data["color"]

            memo.version += 1
            memo.updated_at = _now_dt()
            db.flush()
            return SyncPushResultItem(
                client_id=change.client_id,
                entity_type="memo",
                status="updated",
                server_id=memo.id,
                version=memo.version,
            )

        elif change.action == "delete":
            if not memo or memo.deleted_at is not None:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="memo",
                    status="skipped",
                    server_id=memo.id if memo else None,
                    version=memo.version if memo else None,
                )
            if memo.version != change.version:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="memo",
                    status="conflict",
                    server_id=memo.id,
                    server_version=memo.version,
                    server_data={"content": memo.content},
                )
            now = _now_dt()
            memo.deleted_at = now
            memo.version += 1
            memo.updated_at = now
            db.flush()
            return SyncPushResultItem(
                client_id=change.client_id,
                entity_type="memo",
                status="deleted",
                server_id=memo.id,
                version=memo.version,
            )

        return SyncPushResultItem(client_id=change.client_id, entity_type="memo", status="skipped")

    def _sync_accounting(
        self, db: Session, user_id: int, change: SyncPushChangeItem
    ) -> SyncPushResultItem:
        record = db.scalar(
            select(AccountingRecord).where(
                AccountingRecord.user_id == user_id,
                AccountingRecord.client_id == change.client_id,
            )
        )
        data = change.data or {}

        if change.action == "create":
            if record:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="accounting",
                    status="skipped",
                    server_id=record.id,
                    version=record.version,
                )
            cat_id = data.get("category_id") or 1
            rec_type = data.get("record_type") or "expense"
            amt = Decimal(str(data.get("amount") or "0.01"))
            if amt <= 0:
                amt = Decimal("0.01")

            rec_date = date.today()
            if data.get("record_date"):
                try:
                    rec_date = date.fromisoformat(str(data["record_date"]))
                except Exception:
                    pass

            new_record = AccountingRecord(
                client_id=change.client_id,
                user_id=user_id,
                category_id=cat_id,
                record_type=rec_type,
                amount=amt,
                record_date=rec_date,
                note=data.get("note"),
                version=1,
            )
            db.add(new_record)
            db.flush()
            return SyncPushResultItem(
                client_id=change.client_id,
                entity_type="accounting",
                status="created",
                server_id=new_record.id,
                version=1,
            )

        elif change.action == "update":
            if not record or record.deleted_at is not None:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="accounting",
                    status="conflict",
                    server_id=record.id if record else None,
                    server_version=record.version if record else 0,
                    server_data=None,
                )
            if record.version != change.version:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="accounting",
                    status="conflict",
                    server_id=record.id,
                    server_version=record.version,
                    server_data={
                        "category_id": record.category_id,
                        "record_type": record.record_type,
                        "amount": _format_amount(record.amount),
                        "record_date": record.record_date.isoformat(),
                        "note": record.note,
                    },
                )
            if "category_id" in data and data["category_id"] is not None:
                record.category_id = data["category_id"]
            if "record_type" in data and data["record_type"] is not None:
                record.record_type = data["record_type"]
            if "amount" in data and data["amount"] is not None:
                amt = Decimal(str(data["amount"]))
                if amt > 0:
                    record.amount = amt
            if "record_date" in data and data["record_date"] is not None:
                try:
                    record.record_date = date.fromisoformat(str(data["record_date"]))
                except Exception:
                    pass
            if "note" in data:
                record.note = data["note"]

            record.version += 1
            record.updated_at = _now_dt()
            db.flush()
            return SyncPushResultItem(
                client_id=change.client_id,
                entity_type="accounting",
                status="updated",
                server_id=record.id,
                version=record.version,
            )

        elif change.action == "delete":
            if not record or record.deleted_at is not None:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="accounting",
                    status="skipped",
                    server_id=record.id if record else None,
                    version=record.version if record else None,
                )
            if record.version != change.version:
                return SyncPushResultItem(
                    client_id=change.client_id,
                    entity_type="accounting",
                    status="conflict",
                    server_id=record.id,
                    server_version=record.version,
                    server_data={"amount": _format_amount(record.amount)},
                )
            now = _now_dt()
            record.deleted_at = now
            record.version += 1
            record.updated_at = now
            db.flush()
            return SyncPushResultItem(
                client_id=change.client_id,
                entity_type="accounting",
                status="deleted",
                server_id=record.id,
                version=record.version,
            )

        return SyncPushResultItem(client_id=change.client_id, entity_type="accounting", status="skipped")

    def pull(
        self,
        db: Session,
        user_id: int,
        since: datetime,
        entity_types: Optional[str] = None,
        limit: int = 200,
    ) -> SyncPullResponseData:
        """拉取增量变更。"""
        limit = min(max(1, limit), 500)
        selected_types = (
            [t.strip() for t in entity_types.split(",") if t.strip()]
            if entity_types
            else ["todo", "memo", "accounting"]
        )

        norm_since = _normalize_dt(since)
        changes: List[SyncPullChangeItem] = []

        if "todo" in selected_types:
            todos = db.scalars(
                select(Todo).where(Todo.user_id == user_id, Todo.updated_at >= norm_since)
            ).all()
            for t in todos:
                deleted = t.deleted_at is not None
                data = (
                    None
                    if deleted
                    else {
                        "title": t.title,
                        "description": t.description,
                        "priority": t.priority,
                        "status": t.status,
                        "due_at": _to_iso(t.due_at),
                        "completed_at": _to_iso(t.completed_at),
                        "sort_order": t.sort_order,
                    }
                )
                changes.append(
                    SyncPullChangeItem(
                        entity_type="todo",
                        server_id=t.id,
                        client_id=t.client_id,
                        version=t.version,
                        deleted=deleted,
                        updated_at=_to_iso(t.updated_at) or "",
                        data=data,
                    )
                )

        if "memo" in selected_types:
            memos = db.scalars(
                select(Memo).where(Memo.user_id == user_id, Memo.updated_at >= norm_since)
            ).all()
            for m in memos:
                deleted = m.deleted_at is not None
                data = (
                    None
                    if deleted
                    else {
                        "title": m.title,
                        "content": m.content,
                        "is_pinned": m.is_pinned,
                        "color": m.color,
                    }
                )
                changes.append(
                    SyncPullChangeItem(
                        entity_type="memo",
                        server_id=m.id,
                        client_id=m.client_id,
                        version=m.version,
                        deleted=deleted,
                        updated_at=_to_iso(m.updated_at) or "",
                        data=data,
                    )
                )

        if "accounting" in selected_types:
            records = db.scalars(
                select(AccountingRecord).where(
                    AccountingRecord.user_id == user_id, AccountingRecord.updated_at >= norm_since
                )
            ).all()
            for r in records:
                deleted = r.deleted_at is not None
                data = (
                    None
                    if deleted
                    else {
                        "category_id": r.category_id,
                        "record_type": r.record_type,
                        "amount": _format_amount(r.amount),
                        "record_date": r.record_date.isoformat(),
                        "note": r.note,
                    }
                )
                changes.append(
                    SyncPullChangeItem(
                        entity_type="accounting",
                        server_id=r.id,
                        client_id=r.client_id,
                        version=r.version,
                        deleted=deleted,
                        updated_at=_to_iso(r.updated_at) or "",
                        data=data,
                    )
                )

        # 按 updated_at 升序排列
        changes.sort(key=lambda x: x.updated_at)

        has_more = len(changes) > limit
        if has_more:
            changes = changes[:limit]

        return SyncPullResponseData(
            server_time=_to_iso(_now_dt()) or "",
            has_more=has_more,
            changes=changes,
        )


sync_service = SyncService()
