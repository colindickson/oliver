from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.project_default import ProjectDefaultResponse, ProjectDefaultUpsert
from app.services.project_default_service import ProjectDefaultService

router = APIRouter(prefix="/api/project-defaults", tags=["project_defaults"])


@router.get("", response_model=list[ProjectDefaultResponse])
async def list_project_defaults(
    db: AsyncSession = Depends(get_db),
) -> list[ProjectDefaultResponse]:
    return await ProjectDefaultService(db).list_all()


@router.get("/{project_name}", response_model=ProjectDefaultResponse)
async def get_project_default(
    project_name: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectDefaultResponse:
    return await ProjectDefaultService(db).get_by_project_name(project_name)


@router.put("/{project_name}", response_model=ProjectDefaultResponse)
async def upsert_project_default(
    project_name: str,
    payload: ProjectDefaultUpsert,
    db: AsyncSession = Depends(get_db),
) -> ProjectDefaultResponse:
    pd = await ProjectDefaultService(db).upsert(project_name, payload.default_tags)
    await db.commit()
    return pd
