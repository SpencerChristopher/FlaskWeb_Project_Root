import re
import pytest
import os
from src.server import create_app
from mongoengine import get_db, disconnect, connect
from pymongo.errors import ServerSelectionTimeoutError
from src.models.user import User
from src.models.post import Post
from src.extensions import limiter

@pytest.fixture(scope='session', autouse=True)
def database_connection_check():
    """
    Gatekeeper fixture to check for database connection before running tests.
    """
    if os.environ.get("DOCKER_CONTAINER"):
        mongo_uri = "mongodb://mongo:27017/pytest_appdb"
    else:
        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/pytest_appdb")

    try:
        client = connect(host=mongo_uri, serverSelectionTimeoutMS=2000)
        client.server_info()
        disconnect()
    except ServerSelectionTimeoutError as e:
        pytest.exit(f"Database connection failed: {e}. Aborting tests.")


@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for the test session."""
    # Determine MONGO_URI based on environment
    if os.environ.get("DOCKER_CONTAINER"): # Check if running inside a Docker container
        mongo_uri = "mongodb://mongo:27017/pytest_appdb"
    else:
        mongo_uri = "mongodb://localhost:27017/pytest_appdb"
    os.environ["MONGO_URI"] = mongo_uri
    os.environ['SECRET_KEY'] = 'test-secret-key'

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
        try:
            db.client.drop_database(db.name) # Clean DB before tests
        except ServerSelectionTimeoutError:
            pass

    yield app

    with app.app_context():
        db = get_db()
        try:
            db.client.drop_database(db.name) # Clean DB after tests
        except ServerSelectionTimeoutError:
            pass
        disconnect()

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Resets the Flask-Limiter storage before each test function."""
    # Only reset if the limiter storage has been initialized
    if limiter._storage:
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


@pytest.fixture(autouse=True)
def clean_collections_per_function(app):
    """Cleans up specific collections after each test function."""
    yield
    with app.app_context():
        db = get_db()
        try:
            # Explicitly drop collections that are modified by tests
            User.drop_collection()
            Post.drop_collection()
            from src.models.token_blocklist import TokenBlocklist # Import inside the function
            TokenBlocklist.drop_collection()
            # Add other collections here if they are modified by tests
        except ServerSelectionTimeoutError:
            pass


@pytest.fixture
def login_user_fixture(client):
    def _login_user(username, password):
        response = client.post('/api/auth/login', json={
            'username': username,
            'password': password
        })
        assert response.status_code == 200
        
        # Extract access token from Set-Cookie header
        for cookie_header in response.headers.getlist('Set-Cookie'):
            match = re.search(r'access_token_cookie=([^;]+)', cookie_header)
            if match:
                return match.group(1)
        raise Exception("Access token cookie not found in response headers")
    return _login_user

@pytest.fixture
def get_refresh_token_fixture(client):
    def _get_refresh_token(username, password):
        response = client.post('/api/auth/login', json={
            'username': username,
            'password': password
        })
        assert response.status_code == 200

        # Extract refresh token from Set-Cookie header
        for cookie_header in response.headers.getlist('Set-Cookie'):
            match = re.search(r'refresh_token_cookie=([^;]+)', cookie_header)
            if match:
                return match.group(1)
        raise Exception("Refresh token cookie not found in response headers")
    return _get_refresh_token