"""
Application factory for the Flask web application.

This module defines the `create_app` function responsible for
initializing the Flask application, configuring extensions,
registering blueprints, and setting up error handlers.
"""
import os
from flask import Flask, jsonify, request, g
from werkzeug.middleware.proxy_fix import ProxyFix

from src.utils.logger import setup_logging
from src.extensions import db, bcrypt, jwt

import datetime
import time # Added for retry logic # Add this import
from flask_limiter.errors import RateLimitExceeded # Import RateLimitExceeded
from src.exceptions import APIException, NotFoundException, UnauthorizedException, ForbiddenException, BadRequestException, ValidationError
from mongoengine.errors import NotUniqueError, ValidationError as MongoEngineValidationError
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

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
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Initialize JWTManager immediately after app creation
    app.config["JWT_SECRET_KEY"] = os.environ.get("SECRET_KEY") # Use the existing SECRET_KEY for JWT
    jwt.init_app(app)

    @jwt.unauthorized_loader
    def unauthorized_response(callback_exception):
        return UnauthorizedException("Missing or invalid token.").to_dict(), 401

    @jwt.invalid_token_loader
    def invalid_token_response(callback_exception):
        return UnauthorizedException("Signature verification failed or token is malformed.").to_dict(), 401

    @jwt.revoked_token_loader
    def revoked_token_response(jwt_header, jwt_payload):
        return UnauthorizedException("Token has been revoked.").to_dict(), 401

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_response(callback_exception):
        return UnauthorizedException("Fresh token required.").to_dict(), 401

    # Callback function to check if a JWT has been revoked
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        from src.models.token_blocklist import TokenBlocklist
        jti = jwt_payload["jti"]
        # Use read_concern to ensure the read operation sees the latest data
        token = TokenBlocklist.objects(jti=jti).first()
        return token is not None # Return True if token is in blocklist (revoked)

    # Configure JWT token location (e.g., headers, JSON body)
    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    app.config["JWT_COOKIE_SECURE"] = False # Set to True in production with HTTPS
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True
    app.config["JWT_ACCESS_COOKIE_PATH"] = "/api/"
    app.config["JWT_REFRESH_COOKIE_PATH"] = "/api/auth/refresh"
    app.config["JWT_COOKIE_SAMESITE"] = "Lax" # Or "Strict" or "None" (requires Secure=True)


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
        'host': mongo_uri,
        'port': 27017,
        'db': 'appdb'
    }

    MAX_DB_RETRIES = 5
    DB_RETRY_DELAY_SECONDS = 5
    db_connected = False

    for i in range(MAX_DB_RETRIES):
        try:
            app.logger.info(f"Attempting to connect to MongoDB (attempt {i+1}/{MAX_DB_RETRIES})...")
            db.init_app(app)
            bcrypt.init_app(app)
            app.logger.info("Flask-MongoEngine initialized.")
            app.logger.info("Database connection successful.")
            db_connected = True
            break # Exit loop if connection is successful
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            app.logger.warning(f"MongoDB connection failed: {e}. Retrying in {DB_RETRY_DELAY_SECONDS} seconds...")
            time.sleep(DB_RETRY_DELAY_SECONDS)
        except Exception as e:
            app.logger.error(f"An unexpected error occurred during database initialization: {e}")
            # For unexpected errors, we might not want to retry, or retry differently
            break # Exit loop for unexpected errors

    if not db_connected:
        app.logger.critical("Failed to connect to MongoDB after multiple retries. Exiting application.")
        # Depending on desired behavior, you might want to raise an exception here
        # or exit the application process. For now, we'll just log and let Flask continue
        # which might lead to further errors if DB is truly essential.
        raise ConnectionError("Failed to connect to MongoDB. Please check MONGO_URI and MongoDB server status.")
    # --- End MongoDB Connection ---

    # --- Extensions Initialization ---
    # (db, bcrypt, jwt are initialized here)
    # --- End Extensions Initialization ---

    # Register blueprints here

    # --- Security Headers ---
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response

    # --- Route Registration ---
    from src.routes import main_routes, api_routes, auth_routes, admin_routes
    app.register_blueprint(main_routes.bp)
    app.register_blueprint(api_routes.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(admin_routes.bp)

    # --- Error Handlers ---
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 Not Found: {error}")
        response = NotFoundException("The requested URL was not found on the server.").to_dict()
        return jsonify(response), 404

    @app.errorhandler(RateLimitExceeded) # Specific handler for rate limit exceeded
    def ratelimit_handler(e):
        """
        Handles RateLimitExceeded errors, returning a 429 Too Many Requests response.
        """
        app.logger.warning(f"Rate Limit Exceeded for IP: {request.remote_addr} - {e.description}")
        return jsonify({"error_code": "TOO_MANY_REQUESTS", "message": "Too Many Requests", "details": e.description}), 429

    @app.errorhandler(MongoEngineValidationError)
    def handle_mongoengine_validation_error(error):
        """
        Handles MongoEngine ValidationError, converting it to a BadRequestException.
        """
        details_list = []
        if hasattr(error, 'errors') and isinstance(error.errors, dict):
            for field, err_obj in error.errors.items():
                msg = ""
                if hasattr(err_obj, 'message'):
                    msg = err_obj.message
                else:
                    msg = str(err_obj)
                details_list.append({"loc": [field], "msg": msg})
        else:
            # For generic MongoEngineValidationErrors without specific field errors
            details_list.append({"loc": [], "msg": str(error)})
        details = details_list
        
        app.logger.warning(f"MongoEngine Validation Error: {details}")
        response = BadRequestException("Validation error", details=details).to_dict()
        return jsonify(response), 400

    @app.errorhandler(NotUniqueError)
    def handle_not_unique_error(error):
        """
        Handles MongoEngine NotUniqueError, converting it to a ConflictException.
        """
        app.logger.warning(f"Not Unique Error: {error}")
        response = ConflictException(str(error)).to_dict()
        return jsonify(response), 409

    @app.errorhandler(APIException)
    def handle_api_exception(error):
        """
        Handles custom APIException instances, returning a standardized JSON response.
        """
        log_message = (
            f"API Exception: {error.status_code} - {error.error_code} - {error.message}. "
            f"Method: {request.method}, Path: {request.path}, IP: {request.remote_addr}"
        )
        if error.status_code in [400, 422] and request.is_json:
            try:
                log_message += f", Request Data: {request.json}"
            except Exception:
                log_message += ", Request Data: <unparseable JSON>"
        
        app.logger.warning(log_message, exc_info=True if error.status_code == 500 else False)
        response = error.to_dict()
        return jsonify(response), error.status_code

    @app.errorhandler(ConnectionFailure)
    def handle_pymongo_connection_failure(error):
        """
        Handles pymongo.errors.ConnectionFailure, indicating a database connection issue.
        """
        app.logger.error(f"Database Connection Failure: {error}", exc_info=True)
        response = APIException("Database connection error", status_code=500, error_code="DATABASE_ERROR").to_dict()
        return jsonify(response), 500

    @app.errorhandler(ServerSelectionTimeoutError)
    def handle_server_selection_timeout(error):
        """
        Handles pymongo.errors.ServerSelectionTimeoutError for database connection timeouts.
        """
        app.logger.error(f"Database connection timeout: {error}", exc_info=True)
        response = APIException(
            "Service temporarily unavailable, please try again later.",
            status_code=503,
            error_code="SERVICE_UNAVAILABLE"
        ).to_dict()
        return jsonify(response), 503

    @app.errorhandler(Exception) # Change 500 to Exception
    def internal_error(error):
        """
        Handles unhandled exceptions, returning a generic 500 Internal Server Error.
        """
        log_message = (
            f"Unhandled Exception: {error}. "
            f"Method: {request.method}, Path: {request.path}, IP: {request.remote_addr}"
        )
        app.logger.error(log_message, exc_info=True)
        # For unhandled exceptions, return a generic APIException
        response = APIException().to_dict()
        return jsonify(response), APIException.status_code

    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f"403 Forbidden: {error}")
        response = ForbiddenException(str(error)).to_dict()
        return jsonify(response), 403
    # --- End Error Handlers ---

    return app