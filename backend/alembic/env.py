"""Alembic environment configuration for async SQLAlchemy migrations."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# Import Base and all models so that autogenerate can detect the full schema.
from app.database import Base, DATABASE_URL
import app.models  # noqa: F401 — registers all ORM classes on Base.metadata

# Alembic Config object — provides access to values in alembic.ini.
config = context.config

# Set up Python logging from the alembic.ini [loggers] section.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object autogenerate will diff against.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    In offline mode Alembic does not need an actual database connection; it
    renders migration SQL to stdout or a file instead.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(connectable: AsyncEngine) -> None:
    """Run migrations using an async engine connection."""
    async with connectable.connect() as connection:
        await connection.run_sync(_run_migrations_sync)
    await connectable.dispose()


def _run_migrations_sync(connection: object) -> None:
    """Configure the Alembic context and execute migrations synchronously.

    This function is called via ``run_sync`` from within an async context so
    that Alembic's synchronous migration API works with an async engine.
    """
    context.configure(
        connection=connection,  # type: ignore[arg-type]
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with an async engine."""
    connectable = create_async_engine(
        DATABASE_URL,
        future=True,
    )
    asyncio.run(run_async_migrations(connectable))


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
