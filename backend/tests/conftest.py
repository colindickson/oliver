"""Shared pytest configuration.

Sets DATABASE_URL before any app modules are imported so that
database.py (which reads the variable at module scope) does not raise
a KeyError during test collection.  Individual test modules create
their own in-memory SQLite engines and override the ``get_db``
FastAPI dependency, so the value set here is never actually used to
open a connection.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
