"""API routes for the TaskTemplate resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.task import TaskResponse
from app.schemas.task_template import InstantiatePayload, TemplateCreate, TemplateResponse, TemplateUpdate
from app.services.template_service import TemplateService

router = APIRouter(prefix="/api/templates", tags=["templates"])


async def _get_template_or_404(template_id: int, service: TemplateService) -> object:
    """Return a TaskTemplate or raise 404."""
    template = await service.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[TemplateResponse]:
    """Return all templates, optionally filtered by title search."""
    service = TemplateService(db)
    return await service.list_templates(search=search)


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    body: TemplateCreate,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Create a new task template."""
    service = TemplateService(db)
    return await service.create_template(
        title=body.title,
        description=body.description,
        category=body.category,
        tag_names=body.tags,
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Return a single template by ID."""
    service = TemplateService(db)
    return await _get_template_or_404(template_id, service)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    body: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Update a template. Only provided fields are changed."""
    service = TemplateService(db)
    template = await _get_template_or_404(template_id, service)
    return await service.update_template(
        template=template,
        title=body.title,
        description=body.description,
        category=body.category,
        tag_names=body.tags,
    )


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Delete a template by ID."""
    service = TemplateService(db)
    template = await _get_template_or_404(template_id, service)
    await service.delete_template(template)
    return {"deleted": True}


@router.post("/{template_id}/instantiate", response_model=TaskResponse)
async def instantiate_template(
    template_id: int,
    body: InstantiatePayload,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Create a Task from a template. The task is an independent copy."""
    service = TemplateService(db)
    template = await _get_template_or_404(template_id, service)
    try:
        task = await service.instantiate(
            template=template,
            day_id=body.day_id,
            category_override=body.category,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return task
