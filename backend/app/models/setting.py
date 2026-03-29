"""Setting model — a simple key/value configuration store."""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Setting(Base):
    """A single application-level configuration entry.

    Attributes:
        key: The unique setting name; serves as the primary key.
        value: The setting's string-encoded value.
        version: Optimistic locking version — incremented on every write.
    """

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
