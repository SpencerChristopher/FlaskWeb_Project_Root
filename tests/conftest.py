import pytest
import os
from src.server import create_app
from mongoengine import get_db, disconnect

from src.extensions import limiter

@pytest.fixture(scope='module')
def app():
    """Create and configure a new app instance for each test function."""
    # Set MONGO_URI directly for the test session.
    os.environ["MONGO_URI"] = "mongodb://localhost:27017/pytest_appdb"

    app = create_app()
    app.config.update({
        'TESTING': True,
        'RATELIMIT_STORAGE_URI': 'memory://', # Use in-memory storage for testing
        'RATELIMIT_STRATEGY': 'fixed-window', # Explicitly set strategy
        'RATELIMIT_KEY_FUNC': lambda: "test_key" # Use a fixed key for testing
    })

    # Initialize and configure limiter for testing
    limiter.init_app(app)

    with app.app_context():
        db = get_db()
        db.client.drop_database(db.name)

    yield app

    with app.app_context():
        db = get_db()
        db.client.drop_database(db.name)
        # Reset limiter storage after tests
        limiter.reset()
        disconnect()





