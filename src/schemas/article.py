"""Pydantic schemas for article data validation and DTOs."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import bleach
from .base import ALLOWED_TAGS, ALLOWED_ATTRS


class ArticleCreateUpdate(BaseModel):
    """Schema for creating or updating an article."""

    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    is_published: Optional[bool] = False

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        return bleach.clean(v, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

    @field_validator("summary")
    @classmethod
    def sanitize_summary(cls, v: str) -> str:
        return bleach.clean(v, tags=[], attributes={})


class ArticlePublic(BaseModel):
    """DTO for public-facing article data."""

    id: str
    title: str
    summary: str
    content: str
    slug: str
    is_published: bool
    publication_date: Optional[str] = None
    last_updated: Optional[str] = None
    author_username: str
