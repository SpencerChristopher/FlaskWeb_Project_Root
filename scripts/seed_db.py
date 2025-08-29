"""
Script to seed initial data into the application's MongoDB database.

This script creates a default admin user (if not exists) and sample blog posts.
It requires environment variables for MongoDB connection and admin credentials.
"""
import os
import sys
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.models.user import User
from src.models.post import Post
from src.extensions import db
from flask import Flask
import re

# Load environment variables
with open('.env') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

# --- Password Complexity Validator for Seeding ---
def validate_password_complexity(password: str):
    """Enforces password complexity: 8+ chars, 1 upper, 1 lower, 1 digit."""
    if len(password) < 8:
        raise ValueError('Password must be at least 8 characters long')
    if not re.search(r'[A-Z]', password):
        raise ValueError('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        raise ValueError('Password must contain at least one lowercase letter')
    if not re.search(r'\d', password):
        raise ValueError('Password must contain at least one digit')

# Create a minimal Flask app context
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'host': os.environ.get('MONGO_URI')
}
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dummy-secret-key')
db.init_app(app)

app_context = app.app_context()
app_context.push()

MONGO_URI = os.environ.get('MONGO_URI')
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set!")

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
print(f"The password is: {ADMIN_PASSWORD}")

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise ValueError("ADMIN_USERNAME and ADMIN_PASSWORD must be set in .env")

# Validate the admin password complexity before proceeding
try:
    validate_password_complexity(ADMIN_PASSWORD)
except ValueError as e:
    print(f"Error: Admin password in .env file does not meet complexity requirements: {e}")
    app_context.pop()
    exit(1)

print(f"Attempting to connect to MongoDB at: {MONGO_URI}")
try:
    User.objects.first()
    print("Successfully connected to MongoDB via MongoEngine.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    app_context.pop()
    exit(1)

# --- Seed Admin User ---
admin_user_obj = User.objects(username=ADMIN_USERNAME).first()
if admin_user_obj:
    print(f"Admin user '{ADMIN_USERNAME}' already exists. Skipping.")
else:
    admin_user_obj = User(username=ADMIN_USERNAME, email="admin@example.com", role='admin')
    admin_user_obj.set_password(ADMIN_PASSWORD)
    admin_user_obj.save()
    print(f"Added admin user: {ADMIN_USERNAME}")

# --- Seed Blog Posts ---
if not admin_user_obj:
    print("Admin user not found or created. Cannot seed posts without an author.")
    app_context.pop()
    exit(1)

# Post 1
post1_slug = "laura-ipa"
if Post.objects(slug=post1_slug).first():
    print(f"Blog post '{post1_slug}' already exists. Skipping.")
else:
    post1 = Post(
        title="Laura IPA",
        content="This is a sample blog post about Laura IPA. It's a delicious beer!",
        summary="A refreshing IPA.",
        slug=post1_slug,
        is_published=True,
        author=admin_user_obj
    )
    post1.save()
    print(f"Added blog post: {post1_slug}")

# Post 2
post2_slug = "another-great-beer"
if Post.objects(slug=post2_slug).first():
    print(f"Blog post '{post2_slug}' already exists. Skipping.")
else:
    post2 = Post(
        title="Another Great Beer",
        content="This is another sample blog post about a fantastic beer.",
        summary="Simply amazing.",
        slug=post2_slug,
        is_published=True,
        publication_date=datetime.now(UTC) - timedelta(days=3),
        author=admin_user_obj
    )
    post2.save()
    print(f"Added blog post: {post2_slug}")

print("Database seeding complete.")

app_context.pop()