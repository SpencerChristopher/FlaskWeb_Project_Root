import pytest
from flask import Flask # Import Flask
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from mongoengine import get_db
import logging
import os # Added os import
from src.utils.db_utils import check_db_connection
from src.server import create_app # Keep this import for the log check

def test_database_connection(caplog, monkeypatch): # Removed 'app' fixture
    """
    Tests the database connection, providing specific feedback.
    """
    # Create a dedicated app instance for this test to control its DB settings
    test_app = Flask(__name__)
    test_app.config['MONGODB_SETTINGS'] = {
        'host': 'localhost', # Explicitly set to localhost for host-based testing
        'port': 27017,
        'db': 'appdb'
    }
    # Initialize db extension for this test_app
    from src.extensions import db as test_db_extension, limiter as test_limiter_extension
    test_db_extension.init_app(test_app)
    test_limiter_extension.init_app(test_app)

    with test_app.app_context(): # Use test_app's context
        db = get_db()

        # 1. Is the database server running?
        try:
            db.client.admin.command('ping')
            print("Database server is running.")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            pytest.fail(f"Database server is not responding: {e}")

        # 2. Is the appdb database present?
        try:
            db_list = db.client.list_database_names()
            assert 'appdb' in db_list, "The 'appdb' database does not exist."
            print("'appdb' database is present.")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            pytest.fail(f"Could not list databases: {e}")

        # 3. Was the database connected when the web app started?
        # This part still needs to create the main app to check its logs
        with caplog.at_level(logging.INFO):
            monkeypatch.setenv('MONGO_URI', 'mongodb://localhost:27017/appdb')
            app_instance = create_app() # Create the actual app to check its logs
            pass # No explicit call needed here, just let create_app run

        assert 'Database connection successful.' in caplog.text
        print("Database connection was successful at startup.")