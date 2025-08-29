"""
This module defines the User model for authentication and authorization
using MongoEngine.
"""

from src.extensions import db, bcrypt
import datetime
from src.events import user_deleted


class User(db.Document):
    """
    Represents a user in the application, providing authentication methods.
    Inherits from db.Document to be a MongoEngine model.
    """
    username = db.StringField(required=True, unique=True, max_length=80)
    email = db.EmailField(required=True, unique=True)
    password_hash = db.StringField(required=True)
    created_at = db.DateTimeField(default=datetime.datetime.utcnow)
    role = db.StringField(default='user', choices=['user', 'editor', 'admin'])

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

    def delete(self, *args, **kwargs):
        """
        Overrides the default delete method to dispatch a signal before deletion.
        """
        user_id = str(self.id)
        super().delete(*args, **kwargs)
        user_deleted.send(self, user_id=user_id)

    meta = {
        'collection': 'users',
        'indexes': ['username', 'email']
    }
