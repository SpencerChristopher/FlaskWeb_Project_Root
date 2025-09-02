"""
Script to create an initial administrator user for the application.

This script connects to the MongoDB database and creates a user with
the 'admin' role based on environment variables.
"""
import os
import sys
from dotenv import load_dotenv

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.models.user import User
from scripts.utils import get_flask_app_context, validate_password_complexity

# Load environment variables
load_dotenv()

# Set up Flask app context
app_context = get_flask_app_context()

MONGO_URI = os.environ.get('MONGO_URI')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

if not all([MONGO_URI, ADMIN_USERNAME, ADMIN_PASSWORD]):
    print("Error: MONGO_URI, ADMIN_USERNAME, and ADMIN_PASSWORD must be set in your .env file.")
    app_context.pop()
    exit(1)

# Validate the admin password complexity before proceeding
try:
    validate_password_complexity(ADMIN_PASSWORD)
except ValueError as e:
    print(f"Error: Admin password does not meet complexity requirements: {e}")
    app_context.pop()
    exit(1)

print(f"Attempting to connect to MongoDB at: {MONGO_URI}")
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
    print(f"Admin user '{ADMIN_USERNAME}' created successfully with role 'admin'.")

# Pop the application context
app_context.pop()
