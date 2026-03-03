from pydantic import BaseModel, Field, field_validator
from typing import Optional

class WorkHistoryItem(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: Optional[str] = "Present"
    location: str
    description: Optional[str] = None
    skills: list[str] = Field(default_factory=list)

class SocialLinks(BaseModel):
    github: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    leetcode: Optional[str] = None
    kaggle: Optional[str] = None
    hackthebox: Optional[str] = None

    @field_validator("*")
    @classmethod
    def validate_urls(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("URL must be absolute (start with http:// or https://).")
        return v

class ProfileSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    location: str = Field(..., max_length=100)
    statement: str = Field(..., min_length=10, max_length=2000)
    interests: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    social_links: SocialLinks = Field(default_factory=SocialLinks)
    work_history: list[WorkHistoryItem] = Field(default_factory=list)
    image_url: Optional[str] = None

class ProfilePublic(BaseModel):
    name: str
    location: str
    statement: str
    interests: list[str]
    skills: list[str]
    social_links: SocialLinks
    work_history: list[WorkHistoryItem]
    image_url: Optional[str] = None
    last_updated: Optional[str] = None
