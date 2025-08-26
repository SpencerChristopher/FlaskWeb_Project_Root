"""
Application factory for the Flask web application.

This module defines the `create_app` function responsible for
initializing the Flask application, configuring extensions,
registering blueprints, and setting up error handlers.
"""
import os
from flask import Flask, jsonify
from src.utils.logger import setup_logging
from src.extensions import db, bcrypt, jwt
from src.events import event_dispatcher
import datetime # Add this import
from flask_limiter.errors import RateLimitExceeded # Import RateLimitExceeded

from dotenv import load_dotenv


def create_app():
    """
    Creates and configures the Flask application instance.

    This function sets up:
    - Environment variables loading
    - Static and template folders
    - Secret key
    - Logging
    - MongoDB connection
    - Flask-JWT-Extended initialization
    - Blueprint registration
    - Error handlers

    Returns:
        Flask: The configured Flask application instance.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get the absolute path to the directory containing app.py (the project root)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Set the template_folder and static_folder to the respective directories at the project root level
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static')
    )
    
    # Initialize JWTManager immediately after app creation
    app.config["JWT_SECRET_KEY"] = os.environ.get("SECRET_KEY") # Use the existing SECRET_KEY for JWT
    jwt.init_app(app)


        # Configure JWT token expiry times
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(minutes=15)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(days=7)

    # Initialize Flask-Limiter
    from src.extensions import limiter
    limiter.init_app(app)

    # Load secret key
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    if not app.config['SECRET_KEY']:
        raise ValueError("A SECRET_KEY must be set in the environment variables.")

    # Setup logging for the application
    setup_logging(app)
    app.logger.info('Flask application starting up...')

    # --- MongoDB Connection ---
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        app.logger.error("MONGO_URI environment variable not set!")
        raise ValueError("MONGO_URI environment variable not set!")
    
    app.config['MONGODB_SETTINGS'] = {
        'host': mongo_uri
    }
    try:
        db.init_app(app)
        bcrypt.init_app(app) # Add this line
        app.logger.info("Flask-MongoEngine initialized.")
    except Exception as e:
        app.logger.error(f"Failed to connect to MongoDB: {e}")
        raise ConnectionError("Failed to connect to MongoDB. Please check MONGO_URI and MongoDB server status.") from e
    # --- End MongoDB Connection ---

    # --- Extensions Initialization ---
    # (db, bcrypt, jwt are initialized here)
    # --- End Extensions Initialization ---

    # Register blueprints here

    # Register blueprints here
    from src.routes import main_routes
    from src.routes import auth_routes
    from src.routes import admin_routes
    from src.routes import api_routes # Import api_routes
    import src.listeners # Import listeners to register them

    app.register_blueprint(main_routes.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(api_routes.bp) # Register api_routes

    # --- Error Handlers ---
    @app.errorhandler(404)
    def not_found_error(error):
        """
        Handles 404 Not Found errors by returning a JSON response.

        Args:
            error: The error object.

        Returns:
            Response: A JSON response with a 404 status code.
        """
        app.logger.warning(f"404 Not Found: {error}")
        return jsonify({"error": "Not Found", "message": "The requested URL was not found on the server."}), 404

    @app.errorhandler(RateLimitExceeded) # Specific handler for rate limit exceeded
    def ratelimit_handler(e):
        """
        Handles RateLimitExceeded errors, returning a 429 Too Many Requests response.
        """
        app.logger.warning(f"Rate Limit Exceeded: {e.description}")
        return jsonify({"error": "Too Many Requests", "message": e.description}), 429

    @app.errorhandler(Exception) # Change 500 to Exception
    def internal_error(error):
        """
        Handles 500 Internal Server Errors.

        Args:
            error: The error object.

        Returns:
            Response: A JSON response with a 500 status code.
        """
        # Log the full traceback internally for debugging purposes
        app.logger.error(f"500 Internal Server Error: {error}", exc_info=True)

        response = {
            "status_code": 500,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }

        # Only include detailed error message in debug or testing mode
        if app.debug: # Only show full details in debug mode
            response["details"] = str(error)
        elif app.testing: # In testing, provide a generic error message for details
            response["details"] = "Simulated internal server error during testing."

        return jsonify(response), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        """
        Handles 403 Forbidden errors.

        Args:
            error: The error object.

        Returns:
            Response: A JSON response with a 403 status code.
        """
        app.logger.warning(f"403 Forbidden: {error}")
        return jsonify({"error": "Forbidden", "message": str(error)}), 403
    # --- End Error Handlers ---

    return app