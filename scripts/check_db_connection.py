import os
import sys
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from mongoengine import get_db

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from scripts.utils import get_flask_app_context

def check_db_connection_script():
    """
    Checks the database connection using the MONGO_URI from the environment.
    """
    # Set up Flask app context (this also loads .env and gets MONGO_URI)
    app_context = get_flask_app_context()
    
    mongo_uri = os.environ.get('MONGO_URI')
    print(f"Attempting to connect to MongoDB at: {mongo_uri}")

    try:
        # Get the actual database object within the application context
        current_db = get_db()
        # The 'ping' command is a lightweight way to check the connection
        current_db.client.admin.command('ping')
        print("Database connection successful.")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"Failed to connect to MongoDB: {e}")
        return False
    finally:
        # Ensure the context is popped even if an error occurs
        app_context.pop()

if __name__ == '__main__':
    check_db_connection_script()