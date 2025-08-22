"""
This module defines the User model for authentication and authorization.
"""

from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import UserMixin
from pymongo.database import Database
from bson.objectid import ObjectId
from typing import Optional, Dict, Any

class User(UserMixin):
    """
    Represents a user in the application, providing authentication methods.

    Inherits from UserMixin to integrate with Flask-Login.

    Attributes:
        username (str): The user's unique username.
        email (str): The user's email address.
        password_hash (str): The hashed password for the user.
        _id (ObjectId): The unique identifier from MongoDB.
    """

    def __init__(self, username: str, email: str, password_hash: Optional[str] = None, _id: Optional[ObjectId] = None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self._id = _id

    def set_password(self, password: str) -> None:
        """
        Hashes the provided password and sets it for the user.

        Args:
            password (str): The plain-text password to hash.
        """
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """
        Checks if the provided password matches the user's hashed password.

        Args:
            password (str): The plain-text password to check.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self) -> str:
        """
        Returns the unique ID of the user as a string.
        Required by Flask-Login.

        Returns:
            str: The string representation of the user's ObjectId.
        """
        return str(self._id)

    @staticmethod
    def find_by_username(db: Database, username: str) -> Optional['User']:
        """
        Finds a user in the database by their username.

        Args:
            db (Database): The database instance.
            username (str): The username to search for.

        Returns:
            Optional[User]: A User object if found, otherwise None.
        """
        user_data = db.users.find_one({"username": username})
        if user_data:
            return User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                _id=user_data['_id']
            )
        return None

    @staticmethod
    def find_by_id(db: Database, user_id: str) -> Optional['User']:
        """
        Finds a user in the database by their ID.

        Args:
            db (Database): The database instance.
            user_id (str): The user's unique ID (as a string).

        Returns:
            Optional[User]: A User object if found, otherwise None.
        """
        try:
            user_data = db.users.find_one({"_id": ObjectId(user_id)})
            if user_data:
                return User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    _id=user_data['_id']
                )
            return None
        except Exception:
            return None

    @staticmethod
    def create_user(db: Database, username: str, email: str, password: str) -> Optional['User']:
        """
        Creates a new user in the database.

        Checks if a user with the given username already exists.

        Args:
            db (Database): The database instance.
            username (str): The desired username.
            email (str): The user's email address.
            password (str): The user's plain-text password.

        Returns:
            Optional[User]: The newly created User object, or None if the user already exists.
        """
        if User.find_by_username(db, username):
            return None  # User already exists

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        user_data = {
            "username": new_user.username,
            "email": new_user.email,
            "password_hash": new_user.password_hash
        }
        result = db.users.insert_one(user_data)
        new_user._id = result.inserted_id
        return new_user

