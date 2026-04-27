from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oliver_shared import MAX_TAGS_PER_TASK

from app.exceptions import InvalidOperationError, ProjectDefaultNotFoundError
from app.models.project_default import ProjectDefault


class ProjectDefaultService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_all(self) -> list[ProjectDefault]:
        result = await self._db.execute(
            select(ProjectDefault).order_by(ProjectDefault.project_name)
        )
        return list(result.scalars().all())

    async def get_by_project_name(self, project_name: str) -> ProjectDefault:
        result = await self._db.execute(
            select(ProjectDefault).where(ProjectDefault.project_name == project_name)
        )
        pd = result.scalar_one_or_none()
        if pd is None:
            raise ProjectDefaultNotFoundError(project_name)
        return pd

    async def upsert(self, project_name: str, default_tags: list[str]) -> ProjectDefault:
        if len(default_tags) > MAX_TAGS_PER_TASK:
            raise InvalidOperationError(
                f"A project may have at most {MAX_TAGS_PER_TASK} default tags",
                http_status_code=400,
            )
        result = await self._db.execute(
            select(ProjectDefault).where(ProjectDefault.project_name == project_name)
        )
        pd = result.scalar_one_or_none()
        if pd is None:
            pd = ProjectDefault(project_name=project_name, default_tags=list(default_tags))
            self._db.add(pd)
        else:
            pd.default_tags = list(default_tags)
        await self._db.flush()
        await self._db.refresh(pd)
        return pd
