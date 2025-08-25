"""
This module centralizes the initialization of Flask extensions.

It provides global instances of extensions like MongoEngine, Bcrypt,
and Flask-JWT-Extended, which can be imported and used across the application.
"""
from flask_mongoengine import MongoEngine
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

db = MongoEngine()
bcrypt = Bcrypt()
jwt = JWTManager()