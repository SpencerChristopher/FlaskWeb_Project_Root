import os
# CRITICAL: These must be set BEFORE any other project imports to ensure
# Talisman and other extensions initialize with test-safe defaults.
os.environ.setdefault("FLASK_ENV", "development")
os.environ["TALISMAN_FORCE_HTTPS"] = "false"
# Default E2E base URL for in-container runs when not explicitly set.
if os.environ.get("DOCKER_CONTAINER") in {"1", "true"} and "E2E_BASE_URL" not in os.environ:
    os.environ["E2E_BASE_URL"] = "http://nginx"

import re
import pytest
from flask import Flask
from dotenv import load_dotenv
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

load_dotenv()
from src.server import create_app
from mongoengine import disconnect, connect, get_db
from pymongo.errors import ServerSelectionTimeoutError
from src.models.user import User
from src.models.article import Article
from src.extensions import limiter

def _clear_test_collections() -> None:
    db = get_db()
    db.get_collection(User._get_collection_name()).delete_many({})
    db.get_collection(Article._get_collection_name()).delete_many({})
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
    if "tests\\unit\\" in path or "tests/unit/" in path:
        item.add_marker(pytest.mark.unit)
        return
    if "tests\\integration\\" in path or "tests/integration/" in path:
        item.add_marker(pytest.mark.integration)
        return
    if "tests\\security\\" in path or "tests/security/" in path:
        item.add_marker(pytest.mark.security)
        item.add_marker(pytest.mark.integration)
        return
    if "tests\\infra\\" in path or "tests/infra/" in path:
        item.add_marker(pytest.mark.integration)
        # Inherit specific sub-markers based on filename if needed
        if "smoke" in path:
            item.add_marker(pytest.mark.smoke)
        if "risk" in path or "chaos" in path:
            item.add_marker(pytest.mark.risk)
        return
    if "tests\\e2e\\" in path or "tests/e2e/" in path:
        item.add_marker(pytest.mark.e2e)
        return
    # Default: treat uncategorized files as unit tests so -m selectors keep them
    item.add_marker(pytest.mark.unit)


def pytest_collection_modifyitems(config, items):
    for item in items:
        _add_markers_by_path(item)


@pytest.fixture
def prod_base_url():
    """Returns the live URL for smoke and performance testing."""
    if os.environ.get("DOCKER_CONTAINER") in ["1", "true"]:
        return os.environ.get("PROD_BASE_URL", "http://nginx")
    return os.environ.get("PROD_BASE_URL", "http://localhost:5000")


@pytest.fixture(scope="session")
def base_url(request):
    """
    Provide a stable base URL for e2e tests.
    Prefers explicit env vars, then pytest-base-url option, then sensible defaults.
    """
    env_url = os.environ.get("PYTEST_BASE_URL") or os.environ.get("E2E_BASE_URL")
    if env_url:
        return env_url

    opt_url = getattr(request.config.option, "base_url", None)
    if opt_url:
        return opt_url

    if os.environ.get("DOCKER_CONTAINER") in {"1", "true"}:
        return "http://nginx"
    return "http://localhost:5005"


@pytest.fixture(scope="session", autouse=True)
def database_connection_check():
    """
    Gatekeeper fixture to check for database connection before running tests.
    Can be skipped with SKIP_DB_CHECK=1 for E2E tests where the runner doesn't need DB access.
    """
    if os.environ.get("SKIP_DB_CHECK") == "1":
        return

    mongo_uri = _build_test_mongo_uri(bool(os.environ.get("DOCKER_CONTAINER")))

    try:
        client = connect(
            host=mongo_uri, serverSelectionTimeoutMS=2000, uuidRepresentation="standard"
        )
        client.server_info()
        disconnect()
    except ServerSelectionTimeoutError as e:
        pytest.exit(f"Database connection failed: {e}. Aborting tests.")


@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for the test session."""
    if os.environ.get("SKIP_DB_CHECK") == "1":
        # Return a minimal Flask app to satisfy pytest-flask autouse fixtures
        # This app will not be used by E2E tests but prevents pytest-flask from crashing.
        dummy_app = Flask(__name__)
        dummy_app.config["TESTING"] = True
        yield dummy_app
        return

    # Determine MONGO_URI based on environment
    mongo_uri = _build_test_mongo_uri(bool(os.environ.get("DOCKER_CONTAINER")))
    os.environ["MONGO_URI"] = mongo_uri
    os.environ["SECRET_KEY"] = "test-secret-key"
    
    # In local development/test containers, we must disable HTTPS forcing 
    # because nginx is usually only listening on port 80 (HTTP).
    # Staging/Production will override this via their own env vars.
    os.environ["FLASK_ENV"] = "development"
    os.environ["TALISMAN_FORCE_HTTPS"] = "false"

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            # RATELIMIT_STORAGE_URI is now loaded from .env
            # RATELIMIT_KEY_FUNC is now loaded from extensions
            "RATELIMIT_STRATEGY": "fixed-window",
            "RATELIMIT_DEFAULT": "100 per minute",
        }
    )

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


@pytest.fixture(scope="function")
def setup_users(app):
    """Sets up test users for authentication tests."""
    with app.app_context():
        admin_user = User(username="testadmin", email="admin@example.com", role="admin")
        admin_user.set_password("testpassword")
        admin_user.save()

        regular_user = User(
            username="testuser", email="user@example.com", role="member"
        )
        regular_user.set_password("testpassword")
        regular_user.save()
        yield admin_user, regular_user


@pytest.fixture(autouse=True)
def clean_collections_per_function(app):
    """Cleans up specific collections after each test function."""
    # For host-side E2E runs we skip DB entirely.
    if os.environ.get("SKIP_DB_CHECK") == "1":
        yield
        return
    yield
    if app is None:
        return
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
        response = client.post(
            "/api/auth/login", json={"username": username, "password": password}
        )
        assert response.status_code == 200

        # Extract access token from Set-Cookie header
        for cookie_header in response.headers.getlist("Set-Cookie"):
            match = re.search(r"access_token_cookie=([^;]+)", cookie_header)
            if match:
                return match.group(1)
        raise Exception("Access token cookie not found in response headers")

    return _login_user


@pytest.fixture
def get_refresh_token_fixture(client):
    def _get_refresh_token(username, password):
        response = client.post(
            "/api/auth/login", json={"username": username, "password": password}
        )
        assert response.status_code == 200

        # Extract refresh token from Set-Cookie header
        for cookie_header in response.headers.getlist("Set-Cookie"):
            match = re.search(r"refresh_token_cookie=([^;]+)", cookie_header)
            if match:
                return match.group(1)
        raise Exception("Refresh token cookie not found in response headers")

    return _get_refresh_token


@pytest.fixture
def browser_context_args(browser_context_args):
    """
    Override browser context arguments to include Cloudflare Access headers.
    Supports Service Tokens (ID/Secret) or direct JWT assertions.
    """
    cf_id = os.environ.get("CF_ACCESS_CLIENT_ID")
    cf_secret = os.environ.get("CF_ACCESS_CLIENT_SECRET")
    cf_jwt = os.environ.get("CF_ACCESS_JWT")
    require_cf = os.environ.get("REQUIRE_CF_ACCESS", "").lower() in {"1", "true", "yes"}

    headers = dict(browser_context_args.get("extra_http_headers") or {})
    
    if cf_id and cf_secret:
        headers["CF-Access-Client-ID"] = cf_id
        headers["CF-Access-Client-Secret"] = cf_secret
    
    if cf_jwt:
        headers["Cf-Access-Jwt-Assertion"] = cf_jwt

    if require_cf and not headers:
        pytest.skip("CF Access credentials required for this run (set CF_ACCESS_CLIENT_ID/CF_ACCESS_CLIENT_SECRET).")

    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "extra_http_headers": headers,
    }


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
