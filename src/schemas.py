from pydantic import BaseModel, Field, ValidationInfo, field_validator
from typing import Optional
import bleach


# New import for password_strength
from password_strength import PasswordPolicy

# Define a password policy
# This policy can be customized based on desired complexity rules
# Example: min length 8, require 1 uppercase, 1 lowercase, 1 digit, 1 special character
password_policy = PasswordPolicy.from_names(
    length=8,
    uppercase=1,
    numbers=1,
    special=1
)

# --- Reusable Password Complexity Validator using password_strength ---
def password_strength_validator(cls, v: str, info: ValidationInfo) -> str:
    """
    Enforces password complexity using the password_strength library.
    Provides specific error messages based on failed policy rules.
    """
    test_results = password_policy.test(v)

    if test_results:  # If test_results is not empty, some policies failed
        error_messages = []
        if 'length' in test_results:
            error_messages.append(f'Password must be at least {password_policy.length} characters long.')
        if 'uppercase' in test_results:
            error_messages.append(f'Password must contain at least {password_policy.uppercase} uppercase letter(s).')
        if 'lowercase' in test_results:
            error_messages.append(f'Password must contain at least {password_policy.lowercase} lowercase letter(s).')
        if 'numbers' in test_results:
            error_messages.append(f'Password must contain at least {password_policy.numbers} digit(s).')
        if 'special' in test_results:
            error_messages.append(f'Password must contain at least {password_policy.special} special character(s).')
        if 'strength' in test_results:
            error_messages.append('Password is too weak. Please use a stronger combination of characters.')

        if error_messages:
            raise ValueError(' '.join(error_messages))
        else:
            raise ValueError('Password does not meet complexity requirements.')
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
        return bleach.clean(v, tags=[], attributes={})  # Summary usually plain text

class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str

    _validate_password = field_validator('password')(password_strength_validator)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    _validate_new_password = field_validator('new_password')(password_strength_validator)