"""
Application factory for the Flask web application.

This module composes app bootstrap modules and exposes `create_app`.
"""

from src.app.bootstrap import (
    configure_core_runtime,
    configure_proxy_fix,
    create_flask_app,
    load_environment,
)
from src.app.errors import register_error_handlers
from src.app.routes import register_blueprints
from src.app.security import (
    configure_cors,
    configure_http_security,
    configure_jwt,
    configure_rate_limiter,
)


def create_app():
    """
    Creates and configures the Flask application instance.

    Returns:
        Flask: The configured Flask application instance.
    """
    load_environment()

    app = create_flask_app(__name__)
    configure_proxy_fix(app)
    configure_http_security(app)
    configure_cors(app)
    configure_jwt(app)
    configure_rate_limiter(app)
    configure_core_runtime(app)
    register_blueprints(app)
    register_error_handlers(app)

    return app

