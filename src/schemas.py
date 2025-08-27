from pydantic import BaseModel, Field, validator
from typing import Optional
import bleach

# Define allowed tags and attributes for bleach.clean() at module level
ALLOWED_TAGS = ['p', 'b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre']
ALLOWED_ATTRS = {'a': ['href', 'title']}

class BlogPostCreateUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    is_published: Optional[bool] = False

    @validator('content')
    def sanitize_content(cls, v):
        return bleach.clean(v, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

    @validator('summary')
    def sanitize_summary(cls, v):
        return bleach.clean(v, tags=[], attributes={}) # Summary usually plain text

class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=8)
