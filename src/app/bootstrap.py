"""
Bootstrap and runtime configuration helpers for the Flask app factory.
"""

import os
import time

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
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return Flask(
        import_name,
        template_folder=os.path.join(project_root, "templates"),
        static_folder=os.path.join(project_root, "static"),
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

    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        app.logger.error("MONGO_URI environment variable not set!")
        raise ValueError("MONGO_URI environment variable not set!")

    app.config["MONGODB_SETTINGS"] = {
        "host": mongo_uri,
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
    upload_dir = os.path.join(app.static_folder, "uploads")
    os.makedirs(upload_dir, mode=0o755, exist_ok=True)

