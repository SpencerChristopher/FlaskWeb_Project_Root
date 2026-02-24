"""Blueprint registration helpers."""


def register_blueprints(app) -> None:
    """Register all application blueprints."""
    import src.listeners  # noqa: F401
    from src.routes import content_management_routes, api_routes, auth_routes, main_routes

    app.register_blueprint(main_routes.bp)
    app.register_blueprint(api_routes.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(content_management_routes.bp)

