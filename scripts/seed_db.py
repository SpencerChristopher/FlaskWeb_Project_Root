"""
Script to seed initial data into the application's MongoDB database.

This script creates a default admin user (if not exists) and sample blog posts.
It requires environment variables for MongoDB connection and admin credentials.
"""
import os
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
from src.models.user import User
from src.models.post import Post
from src.extensions import db # Import the db instance
from flask import Flask # Import Flask to create a dummy app for context


# Load environment variables
load_dotenv()

# Create a minimal Flask app context for MongoEngine
# This is necessary because MongoEngine needs an app context to initialize
# when not running within a full Flask application.
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'host': os.environ.get('MONGO_URI')
}
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dummy-secret-key') # Needed for Flask-Login/Bcrypt context
db.init_app(app)

# Push an application context
app_context = app.app_context()
app_context.push()

# Ensure bcrypt is initialized if used outside of a request context
# This is handled by app.extensions, but ensure it's available
# if generate_password_hash is called directly.
# If bcrypt is only used via the User model, this might not be strictly necessary here.

MONGO_URI = os.environ.get('MONGO_URI')
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set!")

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise ValueError("ADMIN_USERNAME and ADMIN_PASSWORD must be set in .env")

print(f"Attempting to connect to MongoDB at: {MONGO_URI}")
try:
    # Test connection by trying to access a collection
    # MongoEngine connects lazily, so we need to force a connection check
    User.objects.first()
    print("Successfully connected to MongoDB via MongoEngine.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    app_context.pop() # Pop context on error
    exit(1)

# --- Seed Admin User ---
admin_user_obj = User.objects(username=ADMIN_USERNAME).first()
if admin_user_obj:
    print(f"Admin user '{ADMIN_USERNAME}' already exists. Skipping.")
else:
    admin_user_obj = User(username=ADMIN_USERNAME, email="admin@example.com")
    admin_user_obj.set_password(ADMIN_PASSWORD) # Use the User model's method
    admin_user_obj.save()
    print(f"Added admin user: {ADMIN_USERNAME}")

# --- Seed Blog Posts ---
# Ensure admin_user_obj is available for post creation
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
        author=admin_user_obj # Assign the User object
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
        publication_date=datetime.now(UTC) - timedelta(days=3), # Example of setting a past date
        author=admin_user_obj # Assign the User object
    )
    post2.save()
    print(f"Added blog post: {post2_slug}")

print("Database seeding complete.")

# Pop the application context
app_context.pop()
