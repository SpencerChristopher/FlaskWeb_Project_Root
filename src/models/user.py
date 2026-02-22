"""
This module defines the User model for authentication and authorization
using MongoEngine.
"""

from src.extensions import db, bcrypt
import datetime

from src.services.roles import (
    ROLE_ADMIN,
    ROLE_CONTENT_ADMIN,
    ROLE_EDITOR,
    ROLE_OPS_ADMIN,
    ROLE_USER,
)


class User(db.Document):
    """
    Represents a user in the application, providing authentication methods.
    Inherits from db.Document to be a MongoEngine model.
    """
    username = db.StringField(required=True, unique=True, max_length=80)
    email = db.EmailField(required=True, unique=True)
    password_hash = db.StringField(required=True)
    created_at = db.DateTimeField(default=datetime.datetime.utcnow)
    role = db.StringField(
        default=ROLE_USER,
        choices=[ROLE_USER, ROLE_EDITOR, ROLE_CONTENT_ADMIN, ROLE_OPS_ADMIN, ROLE_ADMIN],
    )
    token_version = db.IntField(default=0)

    def set_password(self, password: str) -> None:
        """Hashes the provided password and sets it for the user."""
        self.password_hash = bcrypt.generate_password_hash(password).decode(
            'utf-8'
        )

    def check_password(self, password: str) -> bool:
        """Checks if the provided password matches the user's hashed password."""
        return bcrypt.check_password_hash(
            self.password_hash, password
        )

    def to_dict(self) -> dict:
        """
        Serializes the User object to a dictionary for JSON responses.
        """
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "role": self.role
        }

    meta = {
        'collection': 'users',
        'indexes': ['username', 'email']
    }
