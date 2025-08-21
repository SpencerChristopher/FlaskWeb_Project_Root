import os
from flask import Flask, render_template, jsonify
from app.utils.logger import setup_logging
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_login import LoginManager # Import LoginManager

def create_app():
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
    
    try:
        client = MongoClient(mongo_uri)
        app.db = client.get_default_database() # Get the database specified in MONGO_URI
        app.logger.info("Successfully connected to MongoDB!")
    except Exception as e:
        app.logger.error(f"Could not connect to MongoDB: {e}")
        raise
    # --- End MongoDB Connection ---

    # --- Flask-Login Initialization ---
    from app.routes.auth_routes import login_manager # Import login_manager from auth_routes
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        """Handles unauthorized access for the API."""
        return jsonify({'error': 'Authentication required'}), 401
    # --- End Flask-Login Initialization ---

    # Register blueprints here
    from app.routes import main_routes
    from app.routes import auth_routes
    from app.routes import admin_routes
    from app.routes import api_routes # Import api_routes

    app.register_blueprint(main_routes.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(api_routes.bp) # Register api_routes

    # --- Error Handlers ---
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 Not Found: {error}")
        return jsonify({"error": "Not Found", "message": str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 Internal Server Error: {error}")
        return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f"403 Forbidden: {error}")
        return jsonify({"error": "Forbidden", "message": str(error)}), 403
    # --- End Error Handlers ---

    return app