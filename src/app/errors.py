"""
Centralized Flask error-handler registration.
"""

from flask import jsonify, request
from flask_limiter.errors import RateLimitExceeded
from mongoengine.errors import NotUniqueError, ValidationError as MongoEngineValidationError
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from src.exceptions import (
    APIException,
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)


def register_error_handlers(app) -> None:
    """Register all application error handlers."""

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 Not Found: {error}")
        response = NotFoundException("The requested URL was not found on the server.").to_dict()
        return jsonify(response), 404

    @app.errorhandler(RateLimitExceeded)
    def ratelimit_handler(error):
        app.logger.warning(f"Rate Limit Exceeded for IP: {request.remote_addr} - {error.description}")
        return (
            jsonify(
                {
                    "error_code": "TOO_MANY_REQUESTS",
                    "message": "Too Many Requests",
                    "details": error.description,
                }
            ),
            429,
        )

    @app.errorhandler(MongoEngineValidationError)
    def handle_mongoengine_validation_error(error):
        details_list = []
        if hasattr(error, "errors") and isinstance(error.errors, dict):
            for field, err_obj in error.errors.items():
                if hasattr(err_obj, "message"):
                    msg = err_obj.message
                else:
                    msg = str(err_obj)
                details_list.append({"loc": [field], "msg": msg})
        else:
            details_list.append({"loc": [], "msg": str(error)})
        details = details_list

        app.logger.warning(f"MongoEngine Validation Error: {details}")
        response = BadRequestException("Validation error", details=details).to_dict()
        return jsonify(response), 400

    @app.errorhandler(NotUniqueError)
    def handle_not_unique_error(error):
        app.logger.warning(f"Not Unique Error: {error}")
        response = ConflictException(str(error)).to_dict()
        return jsonify(response), 409

    @app.errorhandler(APIException)
    def handle_api_exception(error):
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
        app.logger.error(f"Database Connection Failure: {error}", exc_info=True)
        response = APIException("Database connection error", status_code=500, error_code="DATABASE_ERROR").to_dict()
        return jsonify(response), 500

    @app.errorhandler(ServerSelectionTimeoutError)
    def handle_server_selection_timeout(error):
        app.logger.error(f"Database connection timeout: {error}", exc_info=True)
        response = APIException(
            "Service temporarily unavailable, please try again later.",
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
        ).to_dict()
        return jsonify(response), 503

    @app.errorhandler(Exception)
    def internal_error(error):
        log_message = (
            f"Unhandled Exception: {error}. "
            f"Method: {request.method}, Path: {request.path}, IP: {request.remote_addr}"
        )
        app.logger.error(log_message, exc_info=True)
        response = APIException().to_dict()
        return jsonify(response), APIException.status_code

    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f"403 Forbidden: {error}")
        response = ForbiddenException(str(error)).to_dict()
        return jsonify(response), 403

