import os
import sys
from dotenv import load_dotenv
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from mongoengine import get_db
from flask import Flask

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

# Create a minimal Flask app context for MongoEngine
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'host': 'localhost',
    'port': 27017,
    'db': 'appdb'
}
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dummy-secret-key')

# Initialize MongoEngine
from src.extensions import db
db.init_app(app)

# Push an application context
app_context = app.app_context()
app_context.push()

def check_db_connection_script():
    """
    Checks the database connection and prints the result.
    """
    # Get the actual database object within the application context
    current_db = get_db()
    try:
        current_db.client.admin.command('ping')
        print("Database connection successful.")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"Failed to connect to MongoDB: {e}")
        return False

if __name__ == '__main__':
    check_db_connection_script()

# Pop the application context
app_context.pop()
