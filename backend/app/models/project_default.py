from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class ProjectDefault(Base):
    """Stores per-project default tag lists.

    JSON (not JSONB) for SQLite/PostgreSQL portability.
    Always assign a new list on write: pd.default_tags = list(new_tags)
    Never mutate the list in place — SQLAlchemy won't track the change.
    """

    __tablename__ = "project_defaults"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    default_tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
