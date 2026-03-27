"""Shared mixins for Pydantic schema reuse."""

from typing import Any

from pydantic import BaseModel, field_validator


class TagCoercionMixin(BaseModel):
    """Mixin that coerces tag ORM objects to plain strings for response schemas."""

    @field_validator("tags", mode="before", check_fields=False)
    @classmethod
    def coerce_tags(cls, v: Any) -> list[str]:
        """Convert ORM Tag objects to plain name strings."""
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(item)
            else:
                result.append(item.name)
        return result
