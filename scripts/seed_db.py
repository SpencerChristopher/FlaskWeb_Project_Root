import os
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask_bcrypt import generate_password_hash

# Load environment variables
load_dotenv()

MONGO_URI = os.environ.get('MONGO_URI')
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set!")

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise ValueError("ADMIN_USERNAME and ADMIN_PASSWORD must be set in .env")

try:
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()
    print(f"Successfully connected to MongoDB: {db.name}")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)

# --- Seed Blog Post ---
posts_collection = db.posts

# Check if post already exists to prevent duplicates
if posts_collection.find_one({"slug": "laura-ipa"}):
    print("Blog post 'Laura IPA' already exists. Skipping.")
else:
    laura_ipa_post = {
        "title": "Laura IPA",
        "content": "This is a sample blog post about Laura IPA. It's a delicious beer!",
        "summary": "A refreshing IPA.",
        "slug": "laura-ipa",
        "is_published": True,
        "publication_date": datetime.utcnow(),
        "last_updated": datetime.utcnow(),
        "author_id": "placeholder_author_id"
    }
    posts_collection.insert_one(laura_ipa_post)
    print("Added blog post: Laura IPA")

# New post
if posts_collection.find_one({"slug": "another-great-beer"}):
    print("Blog post 'Another Great Beer' already exists. Skipping.")
else:
    another_beer_post = {
        "title": "Another Great Beer",
        "content": "This is another sample blog post about a fantastic beer.",
        "summary": "Simply amazing.",
        "slug": "another-great-beer",
        "is_published": True,
        "publication_date": datetime.utcnow() - timedelta(days=3),
        "last_updated": datetime.utcnow(),
        "author_id": "placeholder_author_id"
    }
    posts_collection.insert_one(another_beer_post)
    print("Added blog post: Another Great Beer")

# --- Seed Admin User ---
users_collection = db.users

# Check if admin user already exists
if users_collection.find_one({"username": ADMIN_USERNAME}):
    print(f"Admin user '{ADMIN_USERNAME}' already exists. Skipping.")
else:
    hashed_password = generate_password_hash(ADMIN_PASSWORD).decode('utf-8')
    admin_user = {
        "username": ADMIN_USERNAME,
        "email": "admin@example.com", # Placeholder email
        "password_hash": hashed_password,
        "created_at": datetime.utcnow()
    }
    users_collection.insert_one(admin_user)
    print(f"Added admin user: {ADMIN_USERNAME}")

print("Database seeding complete.")
client.close()