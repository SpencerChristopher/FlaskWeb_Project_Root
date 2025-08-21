import os
from dotenv import load_dotenv
from pymongo import MongoClient
from flask_bcrypt import generate_password_hash

# Load environment variables from .env file
load_dotenv()

MONGO_URI = os.environ.get('MONGO_URI')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

if not all([MONGO_URI, ADMIN_USERNAME, ADMIN_PASSWORD]):
    print("Error: MONGO_URI, ADMIN_USERNAME, and ADMIN_PASSWORD must be set in your .env file.")
    exit(1)

try:
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)

# Check if admin user already exists
if db.users.find_one({"username": ADMIN_USERNAME}):
    print(f"Admin user '{ADMIN_USERNAME}' already exists.")
else:
    # Hash the password
    hashed_password = generate_password_hash(ADMIN_PASSWORD).decode('utf-8')
    
    # Insert the new admin user
    db.users.insert_one({
        "username": ADMIN_USERNAME,
        "email": f"{ADMIN_USERNAME}@example.com", # Placeholder email
        "password_hash": hashed_password
    })
    print(f"Admin user '{ADMIN_USERNAME}' created successfully.")

client.close()
