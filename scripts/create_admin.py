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
from src.extensions import db # Import the db instance
from flask import Flask # Import Flask to create a dummy app for context

# Load environment variables
load_dotenv()

# Create a minimal Flask app context for MongoEngine
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'host': os.environ.get('MONGO_URI')
}
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dummy-secret-key') # Needed for Flask-Login/Bcrypt context
db.init_app(app)

# Push an application context
app_context = app.app_context()
app_context.push()

MONGO_URI = os.environ.get('MONGO_URI')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

if not all([MONGO_URI, ADMIN_USERNAME, ADMIN_PASSWORD]):
    print("Error: MONGO_URI, ADMIN_USERNAME, and ADMIN_PASSWORD must be set in your .env file.")
    app_context.pop()
    exit(1)

print(f"Attempting to connect to MongoDB at: {MONGO_URI}")
try:
    # Test connection by trying to access a collection
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
    # Create the new admin user with 'admin' role
    admin_user_obj = User(username=ADMIN_USERNAME, email=f"{ADMIN_USERNAME}@example.com", role='admin')
    admin_user_obj.set_password(ADMIN_PASSWORD) # Use the User model's method
    admin_user_obj.save()
    print(f"Admin user '{ADMIN_USERNAME}' created successfully with role 'admin'.")

# Pop the application context
app_context.pop()