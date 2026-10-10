"""打卡、积分与徽章业务服务层。

严格遵循以下业务与系统铁律：
1. 服务端自主计算打卡日期（Asia/Shanghai），严禁信任客户端传来的日期。
2. 同一用户同一天只能打卡一次（数据库级 uq_checkin_user_date 兜底）。
3. 支持 client_id 幂等防重放：同 client_id 重复提交返回上一次打卡结果，不报错、不重复发放积分。
4. 打卡 5 步原子事务：查当日状态 -> 记录打卡 -> 写积分流水 (+10) -> 更新用户积分余额 -> 徽章自动判定发放，任一失败整体回滚。
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ErrorCode
from app.core.exceptions import BusinessException
from app.core.response import PageData
from app.models import (
    Badge,
    CheckinRecord,
    PointTransaction,
    User,
    UserBadge,
)

logger = logging.getLogger(__name__)

# 内存级幂等暂存：key="user_id:client_id" -> result_dict
_IDEMPOTENT_SUBMISSIONS: Dict[str, Dict[str, Any]] = {}


def _get_tz_now() -> datetime:
    """获取带业务时区的当前时间。"""
    return datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE))


def _to_iso(dt: Optional[datetime]) -> str:
    """格式化时间为 ISO 8601 字符串。"""
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(settings.BUSINESS_TIMEZONE))
    return dt.isoformat()


class CheckinService:
    """打卡与积分徽章服务。"""

    def do_checkin(
        self, db: Session, user: User, client_id: Optional[str] = None, remark: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行打卡（原子事务 + 幂等保障）。"""
        now = _get_tz_now()
        today = now.date()

        # 1. 幂等校验：同一 client_id 重复提交直接返回上一次结果
        if client_id:
            idempotent_key = f"{user.id}:{client_id}"
            if idempotent_key in _IDEMPOTENT_SUBMISSIONS:
                logger.info("[checkin] 命中 client_id 幂等重放: key=%s", idempotent_key)
                return _IDEMPOTENT_SUBMISSIONS[idempotent_key]

        # 2. 查当天是否已打卡
        today_record = db.execute(
            select(CheckinRecord).where(
                CheckinRecord.user_id == user.id,
                CheckinRecord.checkin_date == today,
            )
        ).scalar_one_or_none()

        if today_record:
            logger.warning("[checkin] 重复打卡拦截: user_id=%s date=%s", user.id, today)
            raise BusinessException(
                code=ErrorCode.CHECKIN_ALREADY_DONE,
                message="今天已经打过卡了",
            )

        # 3. 计算连续打卡天数（以服务端实际昨天打卡情况为准）
        yesterday = today - timedelta(days=1)
        yesterday_record = db.execute(
            select(CheckinRecord).where(
                CheckinRecord.user_id == user.id,
                CheckinRecord.checkin_date == yesterday,
            )
        ).scalar_one_or_none()

        if yesterday_record:
            continuous_days = yesterday_record.continuous_days + 1
        else:
            continuous_days = 1

        points_reward = 10  # 每日打卡固定奖励 10 积分
        new_badges_list: List[Dict[str, Any]] = []

        try:
            # 4. 事务 step 1: 写打卡记录
            checkin = CheckinRecord(
                user_id=user.id,
                checkin_date=today,
                checkin_time=now,
                points_earned=points_reward,
                continuous_days=continuous_days,
                remark=remark,
                created_at=now,
            )
            db.add(checkin)
            db.flush()

            # 4. 事务 step 2: 更新用户积分余额
            user.points_balance = (user.points_balance or 0) + points_reward
            db.flush()

            # 4. 事务 step 3: 写积分变动流水
            pt = PointTransaction(
                user_id=user.id,
                change_amount=points_reward,
                balance_after=user.points_balance,
                transaction_type="checkin",
                source_type="checkin",
                source_id=checkin.id,
                description=f"每日打卡第 {continuous_days} 天奖励",
                created_at=now,
            )
            db.add(pt)

            # 4. 事务 step 4: 判定并发放徽章
            total_checkin_days = db.execute(
                select(func.count(CheckinRecord.id)).where(CheckinRecord.user_id == user.id)
            ).scalar_one()

            earned_badge_ids = set(
                db.execute(
                    select(UserBadge.badge_id).where(UserBadge.user_id == user.id)
                ).scalars().all()
            )

            all_active_badges = db.execute(
                select(Badge).where(Badge.status == "active")
            ).scalars().all()

            for badge in all_active_badges:
                if badge.id in earned_badge_ids:
                    continue

                earned = False
                if badge.rule_type == "continuous_checkin" and continuous_days >= badge.rule_value:
                    earned = True
                elif badge.rule_type == "total_checkin" and total_checkin_days >= badge.rule_value:
                    earned = True

                if earned:
                    ub = UserBadge(
                        user_id=user.id,
                        badge_id=badge.id,
                        source_type="checkin",
                        source_id=checkin.id,
                        earned_at=now,
                    )
                    db.add(ub)
                    earned_badge_ids.add(badge.id)
                    new_badges_list.append(
                        {
                            "code": badge.code,
                            "name": badge.name,
                            "icon_url": badge.icon_url,
                        }
                    )
                    logger.info(
                        "[checkin] 用户解锁新徽章: user_id=%s badge=%s(%s)",
                        user.id, badge.name, badge.code,
                    )

            # 4. 事务 step 5: 提交事务
            db.commit()

            result = {
                "checkin_id": checkin.id,
                "checkin_date": today.strftime("%Y-%m-%d"),
                "checkin_time": _to_iso(now),
                "points_earned": points_reward,
                "continuous_days": continuous_days,
                "points_balance": user.points_balance,
                "new_badges": new_badges_list,
            }

            if client_id:
                _IDEMPOTENT_SUBMISSIONS[f"{user.id}:{client_id}"] = result

            return result

        except Exception as exc:
            db.rollback()
            logger.error("[checkin] 打卡事务执行失败已回滚: user_id=%s error=%s", user.id, exc)
            raise

    def get_calendar(self, db: Session, user: User, year: int, month: int) -> Dict[str, Any]:
        """获取按年月的打卡日历数据。"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        records = db.execute(
            select(CheckinRecord)
            .where(
                CheckinRecord.user_id == user.id,
                CheckinRecord.checkin_date >= start_date,
                CheckinRecord.checkin_date < end_date,
            )
            .order_by(CheckinRecord.checkin_date.asc())
        ).scalars().all()

        checkin_days = [r.checkin_date.day for r in records]
        item_list = [
            {
                "checkin_date": r.checkin_date.strftime("%Y-%m-%d"),
                "checkin_time": _to_iso(r.checkin_time),
                "points_earned": r.points_earned,
                "continuous_days": r.continuous_days,
                "remark": r.remark,
            }
            for r in records
        ]

        return {
            "year": year,
            "month": month,
            "checkin_days": checkin_days,
            "month_total": len(records),
            "list": item_list,
        }

    def get_stats(self, db: Session, user: User) -> Dict[str, Any]:
        """获取打卡统计数据。"""
        now = _get_tz_now()
        today = now.date()

        today_record = db.execute(
            select(CheckinRecord).where(
                CheckinRecord.user_id == user.id,
                CheckinRecord.checkin_date == today,
            )
        ).scalar_one_or_none()

        today_checked = today_record is not None

        last_record = db.execute(
            select(CheckinRecord)
            .where(CheckinRecord.user_id == user.id)
            .order_by(CheckinRecord.checkin_date.desc())
            .limit(1)
        ).scalar_one_or_none()

        # 计算连续天数：今天已打卡看今天的，今天未打但昨天打了看昨天的，否则断签为 0
        if today_checked and today_record:
            continuous_days = today_record.continuous_days
        elif last_record and last_record.checkin_date == (today - timedelta(days=1)):
            continuous_days = last_record.continuous_days
        else:
            continuous_days = 0

        total_days = db.execute(
            select(func.count(CheckinRecord.id)).where(CheckinRecord.user_id == user.id)
        ).scalar_one()

        max_continuous = db.execute(
            select(func.max(CheckinRecord.continuous_days)).where(CheckinRecord.user_id == user.id)
        ).scalar_one() or 0

        start_of_month = today.replace(day=1)
        current_month_days = db.execute(
            select(func.count(CheckinRecord.id)).where(
                CheckinRecord.user_id == user.id,
                CheckinRecord.checkin_date >= start_of_month,
            )
        ).scalar_one()

        return {
            "continuous_days": continuous_days,
            "max_continuous_days": max_continuous,
            "total_checkin_days": total_days,
            "current_month_days": current_month_days,
            "last_checkin_date": last_record.checkin_date.strftime("%Y-%m-%d") if last_record else None,
            "today_checked": today_checked,
        }

    def get_points_balance(self, db: Session, user: User) -> Dict[str, Any]:
        """获取用户积分余额与汇总。"""
        now = _get_tz_now()
        today_str = now.date().strftime("%Y-%m-%d")

        today_earned = db.execute(
            select(func.coalesce(func.sum(PointTransaction.change_amount), 0)).where(
                PointTransaction.user_id == user.id,
                PointTransaction.change_amount > 0,
                func.date(PointTransaction.created_at) == today_str,
            )
        ).scalar_one()

        total_earned = db.execute(
            select(func.coalesce(func.sum(PointTransaction.change_amount), 0)).where(
                PointTransaction.user_id == user.id,
                PointTransaction.change_amount > 0,
            )
        ).scalar_one()

        return {
            "points_balance": user.points_balance or 0,
            "today_earned": int(today_earned),
            "total_earned": int(total_earned),
        }

    def get_point_transactions(
        self,
        db: Session,
        user: User,
        page: int = 1,
        page_size: int = 20,
        transaction_type: Optional[str] = None,
    ) -> PageData:
        """分页获取积分流水。"""
        query = select(PointTransaction).where(PointTransaction.user_id == user.id)
        count_query = select(func.count(PointTransaction.id)).where(PointTransaction.user_id == user.id)

        if transaction_type:
            query = query.where(PointTransaction.transaction_type == transaction_type)
            count_query = count_query.where(PointTransaction.transaction_type == transaction_type)

        total = db.execute(count_query).scalar_one()

        records = db.execute(
            query.order_by(PointTransaction.created_at.desc(), PointTransaction.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        items = [
            {
                "id": r.id,
                "change_amount": r.change_amount,
                "balance_after": r.balance_after,
                "transaction_type": r.transaction_type,
                "description": r.description,
                "created_at": _to_iso(r.created_at),
            }
            for r in records
        ]

        return PageData.create(items=items, page=page, page_size=page_size, total=total)

    def get_badges(self, db: Session, user: User) -> Dict[str, Any]:
        """获取全部徽章及当前用户获得状态。"""
        all_badges = db.execute(
            select(Badge).where(Badge.status == "active").order_by(Badge.rule_type, Badge.rule_value)
        ).scalars().all()

        user_badge_map = {
            ub.badge_id: ub.earned_at
            for ub in db.execute(
                select(UserBadge).where(UserBadge.user_id == user.id)
            ).scalars().all()
        }

        badge_items = []
        earned_count = 0

        for b in all_badges:
            earned = b.id in user_badge_map
            earned_at = _to_iso(user_badge_map[b.id]) if earned else None
            if earned:
                earned_count += 1

            badge_items.append(
                {
                    "code": b.code,
                    "name": b.name,
                    "description": b.description,
                    "icon_url": b.icon_url,
                    "rule_type": b.rule_type,
                    "rule_value": b.rule_value,
                    "earned": earned,
                    "earned_at": earned_at,
                }
            )

        return {
            "earned_count": earned_count,
            "total_count": len(all_badges),
            "list": badge_items,
        }


# 单例导出
checkin_service = CheckinService()
