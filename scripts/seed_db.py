"""
Script to seed initial data into the application's MongoDB database.

This script creates a default admin user (if not exists) and sample blog posts.
It requires environment variables for admin credentials.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to the Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.user import User
from src.models.post import Post
from src.models.profile import Profile, WorkHistoryItem
from scripts.utils import get_flask_app_context, validate_password_complexity

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

# --- Seed Profile ---
if Profile.objects.first():
    print("Developer profile already exists. Skipping.")
else:
    work_history = [
        WorkHistoryItem(
            company="Global Tech Solutions",
            role="Senior Systems Architect",
            start_date="2021-06",
            end_date="Present",
            location="Remote / London",
            description="Leading the transition to a decoupled modular monolith architecture on Raspberry Pi hardware.",
            skills=["Python", "Flask", "Docker", "Raspberry Pi"]
        ),
        WorkHistoryItem(
            company="Innovative Startups Inc",
            role="Full Stack Developer",
            start_date="2018-01",
            end_date="2021-05",
            location="Manchester, UK",
            description="Developed high-traffic SPAs using modern JavaScript frameworks and Flask backends.",
            skills=["JavaScript", "REST APIs", "MongoDB"]
        )
    ]
    
    profile = Profile(
        name="Chris Developer",
        location="United Kingdom",
        statement="Passionate Senior Developer focused on building high-performance, secure, and resource-efficient web applications. Expert in Python, Flask, and IoT deployments.",
        interests=["Cloud Computing", "Cybersecurity", "Embedded Systems", "Home Automation"],
        skills=["Python", "Flask", "Docker", "MongoDB", "Linux Admin", "CI/CD"],
        social_links={
            "github": "https://github.com/chris",
            "linkedin": "https://linkedin.com/in/chris",
            "leetcode": "https://leetcode.com/chris",
            "hackthebox": "https://app.hackthebox.com/profile/chris"
        },
        work_history=work_history
    )
    profile.save()
    print("Added developer profile singleton.")

print("Database seeding complete.")

app_context.pop()
