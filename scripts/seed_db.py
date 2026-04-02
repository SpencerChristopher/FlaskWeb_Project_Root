"""
Script to seed initial data into the application's MongoDB database.
Updated for Article Pivot and structured Profile data.
"""
import os
import sys
import argparse
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone
from slugify import slugify

# Add project root to the Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.user import User
from src.models.article import Article
from src.models.profile import Profile, WorkHistoryItem
from scripts.utils import get_flask_app_context

def generate_random_content(min_words=1000, max_words=1500):
    """Generates a block of random 'lorem' text."""
    words = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit", 
             "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore", 
             "magna", "aliqua", "enim", "ad", "minim", "veniam", "quis", "nostrud", 
             "exercitation", "ullamco", "laboris", "nisi", "ut", "aliquip", "ex", "ea", 
             "commodo", "consequat", "duis", "aute", "irure", "dolor", "in", "reprehenderit"]
    
    count = random.randint(min_words, max_words)
    content = " ".join(random.choices(words, k=count))
    return content.capitalize() + "."

def seed_db(heavy=False):
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

    # --- Seed Basic Articles ---
    base_articles = [
        ("Laura IPA", "This is a sample article about Laura IPA. It's a delicious beer!", "A refreshing IPA."),
        ("Another Great Beer", "Simply amazing fantastic beer.", "Amazing.")
    ]

    for title, content, summary in base_articles:
        slug = slugify(title)
        if not Article.objects(slug=slug).first():
            Article(
                title=title,
                content=content,
                summary=summary,
                slug=slug,
                is_published=True,
                author=admin_user_obj,
                publication_date=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 10))
            ).save()
            print(f"Added article: {slug}")

    # --- Heavy Seeding Logic ---
    if heavy:
        print("\n--- Starting Heavy Seeding (Stress Test Data) ---")
        count = 150
        for i in range(count):
            title = f"Stress Test Article {i+1}"
            slug = slugify(title)
            
            if Article.objects(slug=slug).first():
                continue
                
            # Random date over the last 2 years
            random_days = random.randint(0, 730)
            pub_date = datetime.now(timezone.utc) - timedelta(days=random_days)
            
            content = generate_random_content(1000, 1500)
            summary = " ".join(content.split()[:20]) + "..."
            
            Article(
                title=title,
                content=content,
                summary=summary,
                slug=slug,
                is_published=True,
                author=admin_user_obj,
                publication_date=pub_date,
                last_updated=pub_date
            ).save()
            
            if (i + 1) % 50 == 0:
                print(f"Progress: {i+1}/{count} articles seeded...")
        
        print(f"Heavy seeding complete: {count} large articles added.")

    # --- Seed Profile (Upsert) ---
    print("\nSeeding developer profile...")
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed initial data into MongoDB.")
    parser.add_argument("--heavy", action="store_true", help="Seed 150 large articles for performance testing.")
    args = parser.parse_args()
    seed_db(heavy=args.heavy)
