"""Async SQLAlchemy database setup.

Provides engine, session factory, declarative base, and the FastAPI
dependency used to inject a database session into route handlers.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

DATABASE_URL = "sqlite+aiosqlite:////data/oliver.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
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

    Yields:
        An open ``AsyncSession`` that is closed automatically when the
        request context exits.
    """
    async with AsyncSessionLocal() as session:
        yield session
