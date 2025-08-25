"""
Utility module for setting up application logging.

This module provides a function to configure logging for the Flask application,
including file rotation and console output.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """
    Configures logging for the Flask application.

    Logs are written to both a rotating file (app.log) and the console.
    The log level is determined by the 'LOG_LEVEL' environment variable,
    defaulting to INFO.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        logging.Logger: The configured logger instance.
    """
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Ensure the logs directory exists
    log_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'app.log')

    # Create a logger
    logger = logging.getLogger() # Get the root logger
    logger.setLevel(numeric_level)

    # Create handlers
    # File handler - rotates logs after 1MB, keeps 5 backups
    file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
    file_handler.setLevel(numeric_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)

    # Create formatters and add them to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Attach logger to Flask app for easy access
    app.logger = logger
    return logger
