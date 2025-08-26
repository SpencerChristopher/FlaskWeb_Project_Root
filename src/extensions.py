"""
This module centralizes the initialization of Flask extensions.

It provides global instances of extensions like MongoEngine, Bcrypt,
and Flask-JWT-Extended, which can be imported and used across the application.
"""
from flask_mongoengine import MongoEngine
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter # Add this import
from flask_limiter.util import get_remote_address # Add this import

db = MongoEngine()
bcrypt = Bcrypt()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address) # Add this line
