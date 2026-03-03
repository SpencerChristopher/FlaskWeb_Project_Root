from pydantic import BaseModel, Field, field_validator
from .base import password_strength_validator

class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str
    _validate_password = field_validator('password')(password_strength_validator)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    _validate_new_password = field_validator('new_password')(password_strength_validator)

class UserIdentity(BaseModel):
    id: str
    username: str
    role: str
    token_version: int
