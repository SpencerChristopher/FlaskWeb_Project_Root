"""
Script to seed initial data into the application's MongoDB database.
Updated for Article Pivot and structured Profile data.
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
from src.models.article import Article
from src.models.profile import Profile, WorkHistoryItem
from scripts.utils import get_flask_app_context, validate_password_complexity

# Set up Flask app context
app_context = get_flask_app_context()

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

if not all([ADMIN_USERNAME, ADMIN_PASSWORD]):
    print("Error: ADMIN_USERNAME and ADMIN_PASSWORD must be set as environment variables.")
    app_context.pop()
    exit(1)

print("Attempting to verify database connectivity...")
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
    print(f"Admin user '{ADMIN_USERNAME}' already exists.")
else:
    admin_user_obj = User(username=ADMIN_USERNAME, email="admin@example.com", role='admin')
    admin_user_obj.set_password(ADMIN_PASSWORD)
    admin_user_obj.save()
    print(f"Added admin user: {ADMIN_USERNAME}")

# --- Seed Articles (Pivot from Posts) ---
art1_slug = "laura-ipa"
if Article.objects(slug=art1_slug).first():
    print(f"Article '{art1_slug}' already exists. Skipping.")
else:
    art1 = Article(
        title="Laura IPA",
        content="This is a sample article about Laura IPA. It's a delicious beer!",
        summary="A refreshing IPA.",
        slug=art1_slug,
        is_published=True,
        author=admin_user_obj,
        publication_date=datetime.now(timezone.utc)
    )
    art1.save()
    print(f"Added article: {art1_slug}")

art2_slug = "another-great-beer"
if Article.objects(slug=art2_slug).first():
    print(f"Article '{art2_slug}' already exists. Skipping.")
else:
    art2 = Article(
        title="Another Great Beer",
        content="Simply amazing fantastic beer.",
        summary="Amazing.",
        slug=art2_slug,
        is_published=True,
        author=admin_user_obj,
        publication_date=datetime.now(timezone.utc) - timedelta(days=3)
    )
    art2.save()
    print(f"Added article: {art2_slug}")

# --- Seed Profile (Upsert) ---
print("Seeding developer profile...")
work_history = [
    WorkHistoryItem(
        company="Global Tech Solutions",
        role="Senior Systems Architect",
        start_date="2021-06",
        end_date="Present",
        location="Remote / London",
        description="Leading the transition to a decoupled modular monolith architecture.",
        skills=["Python", "Flask", "Docker"]
    )
]

profile = Profile.objects.first()
if not profile:
    profile = Profile(
        name="Chris Developer",
        location="United Kingdom",
        statement="Senior Developer focused on high-performance web applications.",
        interests=["Cloud", "Cybersecurity"],
        skills=["Python", "Flask", "Docker", "MongoDB"],
        social_links={
            "github": "https://github.com/chris",
            "linkedin": "https://linkedin.com/in/chris",
            "hackthebox": "https://app.hackthebox.com/profile/chris"
        },
        work_history=work_history
    )
else:
    profile.name = "Chris Developer"
    profile.location = "United Kingdom"
    profile.social_links = {
        "github": "https://github.com/chris",
        "linkedin": "https://linkedin.com/in/chris",
        "hackthebox": "https://app.hackthebox.com/profile/chris"
    }
    profile.work_history = work_history

profile.save()
print("Developer profile singleton seeded successfully.")

print("Database seeding complete.")
app_context.pop()
