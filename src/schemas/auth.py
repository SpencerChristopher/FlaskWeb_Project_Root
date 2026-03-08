"""Pydantic schemas for authentication and user identity."""

from pydantic import BaseModel, Field, field_validator, ValidationInfo
from .base import password_strength_validator


class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str, info: ValidationInfo) -> str:
        return password_strength_validator(cls, v, info)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str, info: ValidationInfo) -> str:
        return password_strength_validator(cls, v, info)


class UserIdentity(BaseModel):
    id: str
    username: str
    role: str
    token_version: int
