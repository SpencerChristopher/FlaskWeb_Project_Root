"""
Script to seed initial data into the application's MongoDB database.

This script creates a default admin user (if not exists) and sample blog posts.
It requires environment variables for MongoDB connection and admin credentials.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.models.user import User
from src.models.post import Post
from scripts.utils import get_flask_app_context, validate_password_complexity

# Set up Flask app context (this also loads .env)
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
    print(f"Error: Admin password in .env file does not meet complexity requirements: {e}")
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
        publication_date=datetime.now(timezone.utc) - timedelta(days=3),
        author=admin_user_obj
    )
    post2.save()
    print(f"Added blog post: {post2_slug}")

print("Database seeding complete.")

app_context.pop()
