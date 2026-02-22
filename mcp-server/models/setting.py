from sqlalchemy import Column, String

from models.base import Base


class Setting(Base):
    """A single application-level configuration entry.

    Attributes:
        key: The unique setting name; serves as the primary key.
        value: The setting's string-encoded value.
    """

    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
