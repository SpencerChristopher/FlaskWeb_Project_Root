from pydantic import BaseModel, Field, ValidationInfo, field_validator
from typing import Optional
import bleach
import re

# --- Reusable Password Complexity Validator ---
def password_complexity_validator(cls, v: str, info: ValidationInfo) -> str:
    """Enforces password complexity: 8+ chars, 1 upper, 1 lower, 1 digit."""
    if len(v) < 8:
        raise ValueError('Password must be at least 8 characters long')
    if not re.search(r'[A-Z]', v):
        raise ValueError('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', v):
        raise ValueError('Password must contain at least one lowercase letter')
    if not re.search(r'\d', v):
        raise ValueError('Password must contain at least one digit')
    return v

# --- Bleach Configuration ---
ALLOWED_TAGS = ['p', 'b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre']
ALLOWED_ATTRS = {'a': ['href', 'title']}

# --- Pydantic Models ---
class BlogPostCreateUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    is_published: Optional[bool] = False

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        return bleach.clean(v, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

    @field_validator('summary')
    @classmethod
    def sanitize_summary(cls, v: str) -> str:
        return bleach.clean(v, tags=[], attributes={}) # Summary usually plain text

class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str

    _validate_password = field_validator('password')(password_complexity_validator)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    _validate_new_password = field_validator('new_password')(password_complexity_validator)