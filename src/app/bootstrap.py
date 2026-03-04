"""
Bootstrap and runtime configuration helpers for the Flask app factory.
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from werkzeug.middleware.proxy_fix import ProxyFix

from src.extensions import bcrypt, db
from src.utils.db_utils import check_db_connection
from src.utils.logger import setup_logging


def load_environment() -> None:
    """Load environment variables from the local environment and .env file."""
    load_dotenv()


def create_flask_app(import_name: str) -> Flask:
    """Create the base Flask app with project-level static/template paths."""
    project_root = Path(__file__).resolve().parent.parent.parent
    return Flask(
        import_name,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )


def configure_proxy_fix(app: Flask) -> None:
    """Apply ProxyFix based on trusted proxy hop configuration."""
    proxy_x_for = int(os.environ.get("PROXY_FIX_X_FOR", "1"))
    proxy_x_proto = int(os.environ.get("PROXY_FIX_X_PROTO", "1"))
    proxy_x_host = int(os.environ.get("PROXY_FIX_X_HOST", "1"))
    proxy_x_prefix = int(os.environ.get("PROXY_FIX_X_PREFIX", "1"))
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=proxy_x_for,
        x_proto=proxy_x_proto,
        x_host=proxy_x_host,
        x_prefix=proxy_x_prefix,
    )


def configure_core_runtime(app: Flask) -> None:
    """
    Configure secret key, logging, and database connectivity for runtime.
    """
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    if not app.config["SECRET_KEY"]:
        raise ValueError("A SECRET_KEY must be set in the environment variables.")

    setup_logging(app)
    app.logger.info("Flask application starting up...")

    # Build MONGO_URI dynamically
    mongo_user = os.environ.get("MONGO_APP_USER", "webserver")
    mongo_pass = os.environ.get("MONGO_APP_PASSWORD", "password")
    mongo_host = os.environ.get("MONGO_HOST", "mongo")
    mongo_db = os.environ.get("MONGO_APP_DB", "appdb")
    
    # Check if testing mode is active to use test database
    is_testing = bool(app.config.get("TESTING") or os.environ.get("PYTEST_CURRENT_TEST"))
    if is_testing:
        mongo_db = os.environ.get("MONGO_TEST_DB", "pytest_appdb")

    mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:27017/{mongo_db}?authSource={os.environ.get('MONGO_APP_DB', 'appdb')}"
    
    # Configure Redis URL
    redis_host = os.environ.get("REDIS_HOST", "redis")
    redis_pass = os.environ.get("REDIS_PASSWORD", "changeme")
    redis_uri = f"redis://:{redis_pass}@{redis_host}:6379/0"
    app.config["RATELIMIT_STORAGE_URI"] = redis_uri
    os.environ["RATELIMIT_STORAGE_URI"] = redis_uri

    app.config["MONGODB_SETTINGS"] = {
        "host": mongo_uri,
        "uuidRepresentation": "standard",
        "serverSelectionTimeoutMS": int(os.environ.get("MONGO_SERVER_SELECTION_TIMEOUT_MS", 10000)),
        "connectTimeoutMS": int(os.environ.get("MONGO_CONNECT_TIMEOUT_MS", 10000)),
        "socketTimeoutMS": int(os.environ.get("MONGO_SOCKET_TIMEOUT_MS", 10000)),
    }

    max_db_retries = 5
    db_retry_delay_seconds = 5
    db_connected = False

    db.init_app(app)
    bcrypt.init_app(app)

    for i in range(max_db_retries):
        try:
            app.logger.info(f"Attempting to connect to MongoDB (attempt {i + 1}/{max_db_retries})...")
            if check_db_connection(app):
                db_connected = True
                break
        except (ConnectionFailure, ServerSelectionTimeoutError) as err:
            app.logger.warning(
                f"MongoDB connection failed: {err}. Retrying in {db_retry_delay_seconds} seconds..."
            )
        except Exception as err:
            app.logger.error(f"An unexpected error occurred during database initialization: {err}")
            break
        time.sleep(db_retry_delay_seconds)

    if not db_connected:
        app.logger.critical("Failed to connect to MongoDB after multiple retries. Exiting application.")
        raise ConnectionError("Failed to connect to MongoDB. Please check MONGO_URI and MongoDB server status.")

    # Ensure media upload directory exists
    upload_dir = Path(app.static_folder) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True, mode=0o755)

