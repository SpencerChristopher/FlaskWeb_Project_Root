import pytest
from app.server import create_app

@pytest.fixture(scope='function')
def app(monkeypatch):
    """Create and configure a new app instance for each test session."""
    # Use monkeypatch to set the MONGO_URI for the test session.
    # This ensures create_app() reads the correct URI when it runs os.environ.get().
    monkeypatch.setenv("MONGO_URI", "mongodb://webserver:password@localhost:27017/appdb?authSource=admin")

    app = create_app()
    app.config.update({
        'TESTING': True,
    })

    yield app

@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to log test outcomes (pass/fail/skip) to the application logger.
    """
    outcome = yield
    rep = outcome.get_result()

    if rep.when == 'call':
        # Get the logger from the app instance
        # We need to create a temporary app instance to get the logger
        # This is a bit of a workaround as pytest hooks don't directly have app context
        temp_app = create_app()
        logger = temp_app.logger

        test_name = item.nodeid
        test_type = "Routing" # Hardcoded for now, can be dynamic later

        if rep.passed:
            logger.info(f"{test_type} Test - {test_name} - PASSED")
        elif rep.failed:
            logger.error(f"{test_type} Test - {test_name} - FAILED")
        elif rep.skipped:
            logger.info(f"{test_type} Test - {test_name} - SKIPPED")
