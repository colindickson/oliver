from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ProjectDefaultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_name: str
    default_tags: list[str] = []


class ProjectDefaultUpsert(BaseModel):
    default_tags: list[str] = []
