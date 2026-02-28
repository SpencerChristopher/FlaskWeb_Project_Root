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
    strategy="fixed-window"
)

# Redis client for session and token management
# Sourced from the same URI as limiter for infrastructure consolidation
redis_pass = os.environ.get("REDIS_PASSWORD", "changeme")
redis_host = os.environ.get("REDIS_HOST", "redis")
redis_client = redis.from_url(os.environ.get("RATELIMIT_STORAGE_URI", f"redis://:{redis_pass}@{redis_host}:6379/0"))
