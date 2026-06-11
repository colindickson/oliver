"""Pytest fixtures for mcp-server tests.

Imports every model module so SQLAlchemy mapper configuration succeeds when
building an in-memory SQLite schema, and provides a SQLite-backed session that
stands in for the real Postgres session in seam tests.
"""

import importlib
import pkgutil
from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from models.base import Base

# Register every mapped class so string relationships resolve at configure time.
for _module in pkgutil.iter_modules(models.__path__):
    importlib.import_module(f"models.{_module.name}")


@pytest.fixture
def patched_get_session(monkeypatch):
    """Monkeypatch tools.work_log.get_session to use a shared in-memory SQLite DB."""
    import tools.work_log as work_log_module

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def fake_get_session():
        session = TestSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    monkeypatch.setattr(work_log_module, "get_session", fake_get_session)
    # log_call opens its own real Postgres session for audit logging, which is
    # unrelated to the normalization under test — stub it out.
    monkeypatch.setattr(work_log_module, "log_call", lambda *a, **k: None)
    return fake_get_session
