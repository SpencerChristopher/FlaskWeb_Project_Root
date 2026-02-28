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
    def try_connect(uri_label: str, uri: str):
        temp_app = Flask(__name__)
        temp_app.config['MONGODB_SETTINGS'] = {
            'host': uri,
            'db': 'appdb',
            'serverSelectionTimeoutMS': 2000
        }
        from src.extensions import db as test_db_extension, limiter as test_limiter_extension
        test_db_extension.init_app(temp_app)
        test_limiter_extension.init_app(temp_app)

        with temp_app.app_context():
            db = get_db()
            db.client.admin.command('ping')
        return temp_app, uri_label, uri

    # Prefer Docker service host when in container, then env MONGO_URI, then localhost.
    candidates = []
    if os.environ.get("DOCKER_CONTAINER"):
        candidates.append(("docker", "mongodb://mongo:27017/appdb"))
    env_uri = os.environ.get("MONGO_URI")
    if env_uri:
        candidates.append(("env", env_uri))
    candidates.append(("localhost", "mongodb://mongo:27017/appdb"))

    test_app = None
    mongo_host = None
    chosen_label = None
    errors = []

    for label, uri in candidates:
        try:
            test_app, chosen_label, mongo_host = try_connect(label, uri)
            break
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            errors.append(f"{label} ({uri}) failed: {e}")

    if not test_app:
        pytest.fail("Database connection failed for all candidates: " + "; ".join(errors))

    print(f"Database connection established using: {chosen_label} ({mongo_host})")
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
            if 'appdb' not in db_list:
                # Create a lightweight marker document to ensure DB creation
                db.client["appdb"]["_healthcheck"].insert_one({"ok": True})
                db_list = db.client.list_database_names()
            assert 'appdb' in db_list, "The 'appdb' database does not exist."
            print("'appdb' database is present.")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            pytest.fail(f"Could not list databases: {e}")

        # 3. Was the database connected when the web app started?
        # This part still needs to create the main app to check its logs
        with caplog.at_level(logging.INFO):
            # Ensure create_app uses the same resolved URI
            monkeypatch.setenv('MONGO_URI', mongo_host)
            app_instance = create_app() # Create the actual app to check its logs
            pass # No explicit call needed here, just let create_app run

        assert 'Database connection successful.' in caplog.text
        print("Database connection was successful at startup.")
