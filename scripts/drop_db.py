"""
Script to drop the application's MongoDB database.

This is useful for development and testing to reset the database state.
It connects using the MONGO_URI from the .env file.
"""
import os
import sys
from pymongo import MongoClient

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from scripts.utils import get_flask_app_context

def drop_database():
    """
    Connects to MongoDB using MONGO_URI and drops the entire database.
    """
    # get_flask_app_context also loads .env and ensures MONGO_URI is set
    app_context = get_flask_app_context()
    
    mongo_uri = os.environ.get('MONGO_URI')
    print(f"Attempting to connect to MongoDB at: {mongo_uri}")

    try:
        # Use pymongo directly to drop the database
        client = MongoClient(mongo_uri)
        db_name = client.get_default_database().name
        
        client.drop_database(db_name)
        print(f"Database '{db_name}' dropped successfully.")

    except Exception as e:
        print(f"An error occurred while trying to drop the database: {e}")
    finally:
        # Ensure the context is popped
        app_context.pop()

if __name__ == '__main__':
    drop_database()