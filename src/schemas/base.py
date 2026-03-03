from pydantic import ValidationInfo
from password_strength import PasswordPolicy
import bleach

# --- Password Policy ---
password_policy = PasswordPolicy.from_names(
    length=8,
    uppercase=1,
    numbers=1,
    special=1
)

def password_strength_validator(cls, v: str, info: ValidationInfo) -> str:
    """Enforces password complexity."""
    test_results = password_policy.test(v)
    if test_results:
        error_messages = []
        if 'length' in test_results: error_messages.append(f'Password must be at least {password_policy.length} characters long.')
        if 'uppercase' in test_results: error_messages.append(f'Password must contain at least {password_policy.uppercase} uppercase letter(s).')
        if 'numbers' in test_results: error_messages.append(f'Password must contain at least {password_policy.numbers} digit(s).')
        if 'special' in test_results: error_messages.append(f'Password must contain at least {password_policy.special} special character(s).')
        if error_messages: raise ValueError(' '.join(error_messages))
    return v

# --- Sanitization Config ---
ALLOWED_TAGS = ['p', 'b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre']
ALLOWED_ATTRS = {'a': ['href', 'title']}
