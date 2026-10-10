"""记账本业务服务层 (AccountingService)。

对应《接口契约》7.3。
遵循：
1. 记账分类与系统预设分类继承
2. 金额格式严格遵循字符串保留 2 位小数
3. 金额必须 > 0 (1406)，分类类型匹配校验 (1405)
4. client_id 幂等与 version 乐观锁
5. 月度与区间收支汇总
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ErrorCode
from app.core.exceptions import BusinessException
from app.core.response import PageData
from app.models.sync import AccountingCategory, AccountingRecord
from app.schemas.accounting import (
    AccountingCategoryItem,
    AccountingCategoryListData,
    AccountingRecordItem,
    AccountingSummaryData,
    AccountingSummaryGroupItem,
    CreateAccountingRecordRequest,
    UpdateAccountingRecordRequest,
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


class AccountingService:
    """记账本业务处理。"""

    def _to_record_item(self, record: AccountingRecord, category_name: str) -> AccountingRecordItem:
        return AccountingRecordItem(
            id=record.id,
            client_id=record.client_id,
            category_id=record.category_id,
            category_name=category_name,
            record_type=record.record_type,
            amount=_format_amount(record.amount),
            record_date=record.record_date.isoformat(),
            note=record.note,
            version=record.version,
            created_at=_to_iso(record.created_at) or "",
            updated_at=_to_iso(record.updated_at) or "",
        )

    def list_categories(
        self,
        db: Session,
        user_id: int,
        category_type: Optional[str] = None,
    ) -> AccountingCategoryListData:
        """获取记账分类列表（系统默认分类 user_id=NULL + 用户自定义分类）。"""
        stmt = select(AccountingCategory).where(
            or_(AccountingCategory.user_id.is_(None), AccountingCategory.user_id == user_id),
            AccountingCategory.status == "active",
        )
        if category_type:
            stmt = stmt.where(AccountingCategory.category_type == category_type)

        stmt = stmt.order_by(AccountingCategory.sort_order.asc(), AccountingCategory.id.asc())
        rows = db.scalars(stmt).all()

        items = [
            AccountingCategoryItem(
                id=c.id,
                name=c.name,
                category_type=c.category_type,
                icon=c.icon,
                color=c.color,
                sort_order=c.sort_order,
                is_system=(c.user_id is None),
            )
            for c in rows
        ]
        return AccountingCategoryListData(list=items)

    def list_records(
        self,
        db: Session,
        user_id: int,
        record_type: Optional[str] = None,
        category_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageData[AccountingRecordItem]:
        """获取记账明细列表。"""
        stmt = (
            select(AccountingRecord, AccountingCategory.name)
            .join(AccountingCategory, AccountingRecord.category_id == AccountingCategory.id)
            .where(
                AccountingRecord.user_id == user_id,
                AccountingRecord.deleted_at.is_(None),
            )
        )

        if record_type:
            stmt = stmt.where(AccountingRecord.record_type == record_type)
        if category_id:
            stmt = stmt.where(AccountingRecord.category_id == category_id)
        if start_date:
            stmt = stmt.where(AccountingRecord.record_date >= start_date)
        if end_date:
            stmt = stmt.where(AccountingRecord.record_date <= end_date)

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(total_stmt) or 0

        # 按记账所属日期倒序、创建时间倒序、ID 倒序
        stmt = stmt.order_by(
            AccountingRecord.record_date.desc(),
            AccountingRecord.id.desc(),
        ).offset((page - 1) * page_size).limit(page_size)

        rows = db.execute(stmt).all()
        items = [self._to_record_item(rec, cat_name) for rec, cat_name in rows]

        return PageData.create(items=items, total=total, page=page, page_size=page_size)

    def create_record(
        self,
        db: Session,
        user_id: int,
        req: CreateAccountingRecordRequest,
    ) -> AccountingRecordItem:
        """新增记账明细（client_id 幂等）。"""
        # 幂等检查
        existing = db.scalar(
            select(AccountingRecord).where(
                AccountingRecord.user_id == user_id,
                AccountingRecord.client_id == req.client_id,
            )
        )
        if existing:
            cat = db.scalar(select(AccountingCategory).where(AccountingCategory.id == existing.category_id))
            return self._to_record_item(existing, cat.name if cat else "")

        # 校验金额大于 0
        if req.amount <= 0:
            raise BusinessException(ErrorCode.AMOUNT_INVALID)

        # 校验分类存在性（系统分类或属于当前用户）
        category = db.scalar(
            select(AccountingCategory).where(
                AccountingCategory.id == req.category_id,
                or_(AccountingCategory.user_id.is_(None), AccountingCategory.user_id == user_id),
                AccountingCategory.status == "active",
            )
        )
        if not category:
            raise BusinessException(ErrorCode.CATEGORY_NOT_FOUND)

        # 校验 record_type 与 category_type 一致
        if req.record_type != category.category_type:
            raise BusinessException(ErrorCode.CATEGORY_TYPE_MISMATCH)

        record = AccountingRecord(
            client_id=req.client_id,
            user_id=user_id,
            category_id=req.category_id,
            record_type=req.record_type,
            amount=req.amount,
            record_date=req.record_date,
            note=req.note,
            version=1,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return self._to_record_item(record, category.name)

    def update_record(
        self,
        db: Session,
        user_id: int,
        record_id: int,
        req: UpdateAccountingRecordRequest,
    ) -> AccountingRecordItem:
        """修改记账记录（乐观锁版本校验）。"""
        record = db.scalar(
            select(AccountingRecord).where(
                AccountingRecord.id == record_id,
                AccountingRecord.user_id == user_id,
                AccountingRecord.deleted_at.is_(None),
            )
        )
        if not record:
            raise BusinessException(ErrorCode.ACCOUNTING_NOT_FOUND)

        if record.version != req.version:
            raise BusinessException(ErrorCode.SYNC_VERSION_CONFLICT)

        target_cat_id = req.category_id if req.category_id is not None else record.category_id
        target_rec_type = req.record_type if req.record_type is not None else record.record_type

        # 校验分类与类型
        category = db.scalar(
            select(AccountingCategory).where(
                AccountingCategory.id == target_cat_id,
                or_(AccountingCategory.user_id.is_(None), AccountingCategory.user_id == user_id),
                AccountingCategory.status == "active",
            )
        )
        if not category:
            raise BusinessException(ErrorCode.CATEGORY_NOT_FOUND)

        if target_rec_type != category.category_type:
            raise BusinessException(ErrorCode.CATEGORY_TYPE_MISMATCH)

        if req.amount is not None:
            if req.amount <= 0:
                raise BusinessException(ErrorCode.AMOUNT_INVALID)
            record.amount = req.amount

        record.category_id = target_cat_id
        record.record_type = target_rec_type

        if req.record_date is not None:
            record.record_date = req.record_date
        if req.note is not None:
            record.note = req.note

        record.version += 1
        record.updated_at = _now_dt()
        db.commit()
        db.refresh(record)

        return self._to_record_item(record, category.name)

    def delete_record(self, db: Session, user_id: int, record_id: int, version: int) -> None:
        """软删除记账记录（乐观锁版本校验）。"""
        record = db.scalar(
            select(AccountingRecord).where(
                AccountingRecord.id == record_id,
                AccountingRecord.user_id == user_id,
                AccountingRecord.deleted_at.is_(None),
            )
        )
        if not record:
            raise BusinessException(ErrorCode.ACCOUNTING_NOT_FOUND)

        if record.version != version:
            raise BusinessException(ErrorCode.SYNC_VERSION_CONFLICT)

        now = _now_dt()
        record.deleted_at = now
        record.version += 1
        record.updated_at = now
        db.commit()

    def get_summary(
        self,
        db: Session,
        user_id: int,
        start_date: date,
        end_date: date,
        group_by: Optional[str] = "category",
    ) -> AccountingSummaryData:
        """获取记账区间汇总统计（按分类或按日期分组）。"""
        records = db.scalars(
            select(AccountingRecord).where(
                AccountingRecord.user_id == user_id,
                AccountingRecord.deleted_at.is_(None),
                AccountingRecord.record_date >= start_date,
                AccountingRecord.record_date <= end_date,
            )
        ).all()

        total_income = Decimal("0.00")
        total_expense = Decimal("0.00")

        # 汇总总额
        for r in records:
            if r.record_type == "income":
                total_income += r.amount
            elif r.record_type == "expense":
                total_expense += r.amount

        balance = total_income - total_expense

        # 分组计算
        groups = []
        if group_by == "date":
            # 按日期聚合
            date_stmt = (
                select(
                    AccountingRecord.record_date,
                    AccountingRecord.record_type,
                    func.sum(AccountingRecord.amount),
                    func.count(AccountingRecord.id),
                )
                .where(
                    AccountingRecord.user_id == user_id,
                    AccountingRecord.deleted_at.is_(None),
                    AccountingRecord.record_date >= start_date,
                    AccountingRecord.record_date <= end_date,
                )
                .group_by(AccountingRecord.record_date, AccountingRecord.record_type)
                .order_by(AccountingRecord.record_date.desc())
            )
            for r_date, r_type, sum_amt, cnt in db.execute(date_stmt).all():
                groups.append(
                    AccountingSummaryGroupItem(
                        key=r_date.isoformat(),
                        category_id=None,
                        record_type=r_type,
                        amount=_format_amount(sum_amt),
                        count=cnt,
                    )
                )
        else:
            # 默认按分类聚合 (契约 7.3.3)
            cat_stmt = (
                select(
                    AccountingCategory.id,
                    AccountingCategory.name,
                    AccountingCategory.category_type,
                    func.sum(AccountingRecord.amount).label("sum_amt"),
                    func.count(AccountingRecord.id).label("cnt"),
                )
                .join(AccountingCategory, AccountingRecord.category_id == AccountingCategory.id)
                .where(
                    AccountingRecord.user_id == user_id,
                    AccountingRecord.deleted_at.is_(None),
                    AccountingRecord.record_date >= start_date,
                    AccountingRecord.record_date <= end_date,
                )
                .group_by(AccountingCategory.id, AccountingCategory.name, AccountingCategory.category_type)
                .order_by(func.sum(AccountingRecord.amount).desc())
            )
            for cat_id, cat_name, cat_type, sum_amt, cnt in db.execute(cat_stmt).all():
                groups.append(
                    AccountingSummaryGroupItem(
                        key=cat_name,
                        category_id=cat_id,
                        record_type=cat_type,
                        amount=_format_amount(sum_amt),
                        count=cnt,
                    )
                )

        return AccountingSummaryData(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            total_income=_format_amount(total_income),
            total_expense=_format_amount(total_expense),
            balance=_format_amount(balance),
            groups=groups,
        )


accounting_service = AccountingService()
