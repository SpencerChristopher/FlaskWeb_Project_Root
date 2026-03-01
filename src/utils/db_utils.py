from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from mongoengine import get_db


def check_db_connection(app):
    """
    Checks the database connection and logs the result.

    Uses a lightweight ping to validate connectivity.
    """
    with app.app_context():
        db = get_db()
        try:
            db.client.admin.command("ping")
            app.logger.info("Database connection successful.")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            app.logger.error(f"Failed to connect to MongoDB: {e}")
            return False
