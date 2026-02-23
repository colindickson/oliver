"""API routes for the Tag resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tag import Tag
from app.schemas.tag import TagResponse, TagTaskGroup
from app.services.tag_service import TagService

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
async def list_tags(db: AsyncSession = Depends(get_db)) -> list[TagResponse]:
    """Return all tags with task counts."""
    service = TagService(db)
    rows = await service.get_all_tags()
    return [TagResponse(id=tag.id, name=tag.name, task_count=count) for tag, count in rows]


@router.get("/{tag_name}/tasks", response_model=list[TagTaskGroup])
async def get_tasks_for_tag(
    tag_name: str, db: AsyncSession = Depends(get_db)
) -> list[TagTaskGroup]:
    """Return tasks grouped by day for a given tag. 404 if tag not found."""
    from sqlalchemy import select
    normalised = tag_name.strip().lower()
    tag_result = await db.execute(select(Tag).where(Tag.name == normalised))
    tag = tag_result.scalar_one_or_none()
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    service = TagService(db)
    groups = await service.get_tasks_for_tag(tag_name)
    return [TagTaskGroup(date=g["date"], tasks=g["tasks"]) for g in groups]
