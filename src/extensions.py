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
import os
import redis

db = MongoEngine()
bcrypt = Bcrypt()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI"),
    strategy="fixed-window" # Explicitly set strategy
)

# Redis client for session and token management
# Sourced from the same URI as limiter for infrastructure consolidation
redis_client = redis.from_url(os.environ.get("RATELIMIT_STORAGE_URI", "redis://redis:6379/0"))
