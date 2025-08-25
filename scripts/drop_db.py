"""
Script to drop the application's MongoDB database.

This is useful for development and testing to reset the database state.
It connects using the MONGO_URI from the .env file.
"""
import os
from dotenv import load_dotenv
from src.extensions import db
from flask import Flask
from pymongo import MongoClient # Use pymongo directly for dropping database

# Load environment variables
load_dotenv()

MONGO_URI = os.environ.get('MONGO_URI')
if not MONGO_URI:
    print("Error: MONGO_URI must be set in your .env file.")
    exit(1)

# Create a minimal Flask app context for MongoEngine
# This is necessary because MongoEngine needs an app context to initialize
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'host': MONGO_URI
}
# SECRET_KEY is not strictly needed for dropping DB, but good for consistency
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dummy-secret-key') 
db.init_app(app)

# Push an application context
app_context = app.app_context()
app_context.push()

print(f"Attempting to connect to MongoDB at: {MONGO_URI}")
try:
    # Use pymongo directly to drop the database
    client = MongoClient(MONGO_URI)
    db_name = client.get_default_database().name # Get the database name from the URI
    client.drop_database(db_name)
    print(f"Database '{db_name}' dropped successfully.")
except Exception as e:
    print(f"Error dropping database: {e}")
    app_context.pop()
    exit(1)

# Pop the application context
app_context.pop()
