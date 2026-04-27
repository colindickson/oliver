from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.types import JSON

from models.base import Base


class ProjectDefault(Base):
    __tablename__ = "project_defaults"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(255), unique=True, nullable=False)
    default_tags = Column(JSON, nullable=False, default=list)

    __table_args__ = (
        UniqueConstraint("project_name", name="uq_project_defaults_project_name"),
    )
