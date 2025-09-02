"""
Utility functions for the scripts in this directory.
"""
import os
import sys
import re
from flask import Flask
from dotenv import load_dotenv

def get_flask_app_context():
    """
    Initializes a minimal Flask app and pushes an application context.

    This allows standalone scripts to use extensions like MongoEngine
    that are initialized within the main Flask application factory.

    Returns:
        A Flask application context that has been pushed.
    """
    # Add project root to the Python path to allow imports from 'src'
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Now that the path is set, we can import extensions
    from src.extensions import db

    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        raise ValueError("MONGO_URI must be set in the .env file.")

    app.config['MONGODB_SETTINGS'] = {'host': mongo_uri}
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dummy-secret-key')

    db.init_app(app)

    app_context = app.app_context()
    app_context.push()

    return app_context

def validate_password_complexity(password: str):
    """Enforces password complexity: 8+ chars, 1 upper, 1 lower, 1 digit, 1 special char."""
    if len(password) < 8:
        raise ValueError('Password must be at least 8 characters long')
    if not re.search(r'[A-Z]', password):
        raise ValueError('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        raise ValueError('Password must contain at least one lowercase letter')
    if not re.search(r'\d', password):
        raise ValueError('Password must contain at least one digit')
    if not re.search(r'[\W_]', password): # \W is any non-alphanumeric character
        raise ValueError('Password must contain at least one special character')
