import re
import pytest
import os
from dotenv import load_dotenv
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

load_dotenv()
# Ensure test env disables HTTPS redirects before app creation
os.environ.setdefault('FLASK_ENV', 'development')
os.environ['TALISMAN_FORCE_HTTPS'] = 'false'
from src.server import create_app
from mongoengine import disconnect, connect, get_db
from pymongo.errors import ServerSelectionTimeoutError
from src.models.user import User
from src.models.post import Post
from src.extensions import limiter


def _clear_test_collections() -> None:
    db = get_db()
    db.get_collection(User._get_collection_name()).delete_many({})
    db.get_collection(Post._get_collection_name()).delete_many({})
    from src.models.token_blocklist import TokenBlocklist
    from src.models.profile import Profile

    db.get_collection(TokenBlocklist._get_collection_name()).delete_many({})
    db.get_collection(Profile._get_collection_name()).delete_many({})

def _build_test_mongo_uri(in_container: bool) -> str:
    if in_container:
        app_user = os.environ.get("MONGO_APP_USER")
        app_password = os.environ.get("MONGO_APP_PASSWORD")
        app_db = os.environ.get("MONGO_APP_DB", "appdb")
        test_db = os.environ.get("MONGO_TEST_DB", "pytest_appdb")
        base_mongo_uri = os.environ.get("MONGO_URI")

        if app_user and app_password:
            return f"mongodb://{app_user}:{app_password}@mongo:27017/{test_db}?authSource={app_db}"
        if base_mongo_uri:
            parsed = urlparse(base_mongo_uri)
            query = dict(parse_qsl(parsed.query, keep_blank_values=True))
            query.setdefault("authSource", app_db)
            return urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    f"/{test_db}",
                    parsed.params,
                    urlencode(query),
                    parsed.fragment,
                )
            )
        return "mongodb://mongo:27017/pytest_appdb"

    return os.environ.get("PYTEST_MONGO_URI", "mongodb://mongo:27017/pytest_appdb")

def _add_markers_by_path(item):
    path = str(item.fspath)
    if "tests\\risk_tests\\" in path or "tests/risk_tests/" in path:
        item.add_marker(pytest.mark.risk)
        item.add_marker(pytest.mark.integration)
        return
    if "tests\\api_tests\\" in path or "tests/api_tests/" in path:
        item.add_marker(pytest.mark.integration)
        return
    if "tests\\security_tests\\" in path or "tests/security_tests/" in path:
        item.add_marker(pytest.mark.security)
        item.add_marker(pytest.mark.integration)
        return
    if "tests\\service_tests\\" in path or "tests/service_tests/" in path:
        item.add_marker(pytest.mark.integration)
        return
    if "tests\\routing_tests\\" in path or "tests/routing_tests/" in path:
        item.add_marker(pytest.mark.integration)
        return
    if "tests\\page_content_test\\" in path or "tests/page_content_test/" in path:
        item.add_marker(pytest.mark.integration)
        return
    if "tests\\test_database_connection.py" in path or "tests/test_database_connection.py" in path:
        item.add_marker(pytest.mark.integration)
        return
    item.add_marker(pytest.mark.unit)

def pytest_collection_modifyitems(config, items):
    for item in items:
        _add_markers_by_path(item)

@pytest.fixture(scope='session', autouse=True)
def database_connection_check():
    """
    Gatekeeper fixture to check for database connection before running tests.
    """
    mongo_uri = _build_test_mongo_uri(bool(os.environ.get("DOCKER_CONTAINER")))

    try:
        client = connect(host=mongo_uri, serverSelectionTimeoutMS=2000, uuidRepresentation='standard')
        client.server_info()
        disconnect()
    except ServerSelectionTimeoutError as e:
        pytest.exit(f"Database connection failed: {e}. Aborting tests.")


@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for the test session."""
    # Determine MONGO_URI based on environment
    mongo_uri = _build_test_mongo_uri(bool(os.environ.get("DOCKER_CONTAINER")))
    os.environ["MONGO_URI"] = mongo_uri
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('TALISMAN_FORCE_HTTPS', 'false')

    app = create_app()
    app.config.update({
        'TESTING': True,
        # RATELIMIT_STORAGE_URI is now loaded from .env
        # RATELIMIT_KEY_FUNC is now loaded from extensions
        'RATELIMIT_STRATEGY': 'fixed-window',
        'RATELIMIT_DEFAULT': '100 per minute'
    })

    # Initialize and configure limiter for testing
    limiter.init_app(app)

    # Establish an application context before yielding the app
    with app.app_context():
        try:
            _clear_test_collections()
        except ServerSelectionTimeoutError:
            pass

    yield app

    with app.app_context():
        try:
            _clear_test_collections()
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

        regular_user = User(username='testuser', email='user@example.com', role='member')
        regular_user.set_password('testpassword')
        regular_user.save()
        yield admin_user, regular_user


@pytest.fixture(autouse=True)
def clean_collections_per_function(app):
    """Cleans up specific collections after each test function."""
    yield
    with app.app_context():
        try:
            # Explicitly drop collections that are modified by tests
            _clear_test_collections()
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


@pytest.fixture
def signal_tracker():
    """
    A fixture that allows capturing and tracking emitted Blinker signals.
    Usage:
        with signal_tracker(my_signal) as tracker:
            call_business_logic()
            assert tracker.called
            assert tracker.data['key'] == 'value'
    """
    from contextlib import contextmanager

    class Tracker:
        def __init__(self):
            self.called = False
            self.calls = []
            self.data = None
            self.sender = None

        def handler(self, sender, **kwargs):
            self.called = True
            self.sender = sender
            self.calls.append(kwargs)
            self.data = kwargs

    @contextmanager
    def _tracker(signal):
        t = Tracker()
        signal.connect(t.handler, weak=False)
        try:
            yield t
        finally:
            signal.disconnect(t.handler)

    return _tracker
