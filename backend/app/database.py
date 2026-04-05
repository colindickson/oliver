"""Async SQLAlchemy database setup.

Provides engine, session factory, declarative base, and the FastAPI
dependency used to inject a database session into route handlers.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request.

    The explicit rollback in the ``finally`` block is a safety net: if the
    route handler raises before committing, any unflushed changes are
    discarded.  Rollback after commit is a no-op in SQLAlchemy, so this
    is harmless when the handler succeeds.

    Yields:
        An open ``AsyncSession`` that is closed automatically when the
        request context exits.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
