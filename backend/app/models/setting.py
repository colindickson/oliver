"""Setting model — a simple key/value configuration store."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Setting(Base):
    """A single application-level configuration entry.

    Attributes:
        key: The unique setting name; serves as the primary key.
        value: The setting's string-encoded value.
    """

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
