"""数据库声明基类、异步引擎与会话工厂。

关键点：
- ``Base``：SQLAlchemy 2.0 声明基类，所有模型继承它。
- ``JSONB``：自定义类型，PostgreSQL 下编译为 ``JSONB``，SQLite 下编译为 ``JSON``，
  保证单一代码库在「生产 PostgreSQL」与「本地 / 测试 SQLite」之间可移植验证。
- ``engine`` / ``AsyncSessionLocal``：基于 ``settings.DATABASE_URL`` 的异步引擎与会话工厂。
"""

from __future__ import annotations

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import JSONB as _PGJSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的声明基类。"""


class JSONB(_PGJSONB):
    """可移植的 JSONB 类型。

    - PostgreSQL：编译为 ``JSONB``（生产目标）。
    - SQLite：编译为 ``JSON``（本地 / 测试验证用，避免引入不可移植写法）。
    """


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_: JSONB, compiler, **kw) -> str:  # noqa: D401, ANN001
    """SQLite 方言下将 JSONB 降级为 JSON。"""
    return "JSON"


# 异步引擎（懒连接，导入时不建立真实连接，仅在首次使用时连库）
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# 会话工厂：请求级会话，提交后不自动过期对象，便于序列化返回
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
