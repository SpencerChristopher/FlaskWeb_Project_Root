from pydantic import BaseModel, Field, field_validator
from typing import Optional

_MAX_URL_LENGTH = 2048

def _validate_url(value: str) -> str:
    if not value.startswith(("http://", "https://")):
        raise ValueError("URL must be absolute (start with http:// or https://).")
    if len(value) > _MAX_URL_LENGTH:
        raise ValueError("URL exceeds maximum length.")
    return value

class WorkHistoryItem(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: Optional[str] = "Present"
    location: str
    description: Optional[str] = None
    skills: list[str] = Field(default_factory=list)

class ProfileSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    location: str = Field(..., max_length=100)
    statement: str = Field(..., min_length=10, max_length=2000)
    interests: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    social_links: dict[str, str] = Field(default_factory=dict)
    work_history: list[WorkHistoryItem] = Field(default_factory=list)
    image_url: Optional[str] = None

    @field_validator("social_links")
    @classmethod
    def validate_social_links(cls, v: dict[str, str]) -> dict[str, str]:
        cleaned: dict[str, str] = {}
        for key, url in v.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("Social link keys must be non-empty strings.")
            if not isinstance(url, str) or not url.strip():
                raise ValueError("Social link URLs must be non-empty strings.")
            cleaned[key] = _validate_url(url.strip())
        return cleaned

class ProfilePublic(BaseModel):
    name: str
    location: str
    statement: str
    interests: list[str]
    skills: list[str]
    social_links: dict[str, str]
    work_history: list[WorkHistoryItem]
    image_url: Optional[str] = None
    last_updated: Optional[str] = None
