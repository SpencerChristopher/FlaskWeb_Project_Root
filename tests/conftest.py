import pytest
import os
from src.server import create_app
from mongoengine import get_db, disconnect
from src.models.user import User
from src.models.post import Post
from src.extensions import limiter

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for the test session."""
    os.environ["MONGO_URI"] = "mongodb://localhost:27017/pytest_appdb"

    app = create_app()
    app.config.update({
        'TESTING': True,
        'RATELIMIT_STORAGE_URI': 'memory://',
        'RATELIMIT_STRATEGY': 'fixed-window',
        'RATELIMIT_KEY_FUNC': lambda: "test_key",
        'RATELIMIT_DEFAULT': '100 per minute'
    })

    # Initialize and configure limiter for testing
    limiter.init_app(app)

    # Establish an application context before yielding the app
    with app.app_context():
        db = get_db()
        db.client.drop_database(db.name) # Clean DB before tests

    yield app

    with app.app_context():
        db = get_db()
        db.client.drop_database(db.name) # Clean DB after tests
        disconnect()

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Resets the Flask-Limiter storage before each test function."""
    limiter.reset()

@pytest.fixture(scope='function')
def setup_users(app):
    """Sets up test users for authentication tests."""
    with app.app_context():
        admin_user = User(username='testadmin', email='admin@example.com', role='admin')
        admin_user.set_password('testpassword')
        admin_user.save()

        regular_user = User(username='testuser', email='user@example.com', role='user')
        regular_user.set_password('testpassword')
        regular_user.save()
        yield admin_user, regular_user
        admin_user.delete()
        regular_user.delete()

@pytest.fixture(autouse=True)
def cleanup_posts():
    """Cleans up all Post objects after each test function."""
    Post.drop_collection()





