"""
Script to create an initial administrator user for the application.

This script connects to the MongoDB database and creates a user with
the 'admin' role based on environment variables.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to the Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.user import User
from scripts.utils import get_flask_app_context, validate_password_complexity

# The get_flask_app_context() utility will handle loading the .env file
# in local development environments.

# Set up Flask app context
app_context = get_flask_app_context()

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

if not all([ADMIN_USERNAME, ADMIN_PASSWORD]):
    print("Error: ADMIN_USERNAME and ADMIN_PASSWORD must be set as environment variables or in .env file.")
    app_context.pop()
    exit(1)

# Validate the admin password complexity before proceeding
try:
    validate_password_complexity(ADMIN_PASSWORD)
except ValueError as e:
    print(f"Error: Admin password does not meet complexity requirements: {e}")
    app_context.pop()
    exit(1)

print("Attempting to verify database connectivity...")
try:
    # A simple query to check the connection
    User.objects.first()
    print("Successfully connected to MongoDB via MongoEngine.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    app_context.pop()
    exit(1)

# Check if admin user already exists
admin_user_obj = User.objects(username=ADMIN_USERNAME).first()
if admin_user_obj:
    print(f"Admin user '{ADMIN_USERNAME}' already exists.")
else:
    admin_user_obj = User(username=ADMIN_USERNAME, email=f"{ADMIN_USERNAME}@example.com", role='admin')
    admin_user_obj.set_password(ADMIN_PASSWORD)
    admin_user_obj.save()
    print(f"Admin user {ADMIN_USERNAME} created successfully with role 'admin'.")

# Pop the application context
app_context.pop()
