"""数据库连接与会话管理。

- 统一使用 SQLAlchemy 2.0 风格。
- local 可用 SQLite，test/prod 使用 PostgreSQL。
- 通过 get_db 依赖注入提供会话，请求结束自动关闭。
"""

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""

    pass


def _build_engine():
    """按数据库类型构建引擎。"""
    if settings.is_sqlite:
        # SQLite 不支持连接池参数，且需允许跨线程（TestClient 场景）
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            connect_args={"check_same_thread": False},
        )

        # 开启外键约束（SQLite 默认关闭）
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    return create_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
    )


engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：提供数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
