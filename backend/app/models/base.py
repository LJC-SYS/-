"""ORM 模型公共基类与混入。

统一约定（对应《数据库表设计》1.2 通用设计约定）：
- 主键统一 BIGINT，名为 id
- 时间统一带时区
- 所有业务表含 created_at / updated_at
- 需同步的表含 version / deleted_at
"""

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

__all__ = ["Base", "TimestampMixin", "SoftDeleteMixin", "VersionMixin"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    """创建/更新时间混入。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=_utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=_utcnow,
        onupdate=_utcnow,
        comment="更新时间",
    )


class VersionMixin:
    """乐观锁版本号混入，用于离线同步冲突检测。"""

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="乐观锁和同步版本",
    )


class SoftDeleteMixin:
    """软删除混入。

    待办、备忘录、记账使用软删除，保证离线同步能感知删除操作。
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="软删除时间",
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class PkMixin:
    """主键混入。

    使用 BigInteger().with_variant(Integer, "sqlite")：
    - PostgreSQL 下为 BIGINT，符合《数据库表设计》约定
    - SQLite 下退化为 INTEGER，因为 SQLite 只有 INTEGER PRIMARY KEY 才支持自增
    这样本地用 SQLite 开发、线上用 PG，两边行为一致。
    """

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        comment="主键",
    )
