"""
Centralized Flask error-handler registration.
"""

from flask import jsonify, request
from flask_limiter.errors import RateLimitExceeded
from mongoengine.errors import (
    NotUniqueError,
    ValidationError as MongoEngineValidationError,
)
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pydantic import ValidationError as PydanticValidationError

from src.exceptions import (
    APIException,
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    InfrastructureException,  # Import the new base infrastructure exception
)


def register_error_handlers(app) -> None:
    """Register all application error handlers."""

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 Not Found: {error}")
        response = NotFoundException(
            "The requested URL was not found on the server."
        ).to_dict()
        return jsonify(response), 404

    @app.errorhandler(RateLimitExceeded)
    def ratelimit_handler(error):
        app.logger.warning(
            f"Rate Limit Exceeded for IP: {request.remote_addr} - {error.description}"
        )
        response = {
            "error_code": "TOO_MANY_REQUESTS",
            "message": "Too Many Requests",
            "details": [
                {"loc": [], "msg": error.description, "type": "rate_limit_exceeded"}
            ],
        }
        return jsonify(response), 429

    @app.errorhandler(PydanticValidationError)
    def handle_pydantic_validation_error(error):
        # Pydantic v2 .errors() returns exactly what we want: list of dicts with loc, msg, type
        # We explicitly strip 'input' to avoid leaking passwords or PII in error responses
        details = [
            {k: v for k, v in err.items() if k != "input"} for err in error.errors()
        ]
        app.logger.warning(f"Pydantic Validation Error: {details}")
        response = BadRequestException("Invalid data", details=details).to_dict()
        return jsonify(response), 400

    @app.errorhandler(MongoEngineValidationError)
    def handle_mongoengine_validation_error(error):
        details_list = []
        if hasattr(error, "errors") and isinstance(error.errors, dict):
            for field, err_obj in error.errors.items():
                msg = getattr(err_obj, "message", str(err_obj))
                details_list.append(
                    {"loc": [field], "msg": msg, "type": "value_error.mongoengine"}
                )
        else:
            details_list.append(
                {"loc": [], "msg": str(error), "type": "value_error.mongoengine"}
            )

        app.logger.warning(f"MongoEngine Validation Error: {details_list}")
        response = BadRequestException(
            "Validation error", details=details_list
        ).to_dict()
        return jsonify(response), 400

    @app.errorhandler(NotUniqueError)
    def handle_not_unique_error(error):
        app.logger.warning(f"Not Unique Error: {error}")
        response = ConflictException(
            "A resource with this identifier already exists."
        ).to_dict()
        return jsonify(response), 409

    @app.errorhandler(APIException)
    def handle_api_exception(error):
        log_message = (
            f"API Exception: {error.status_code} - {error.error_code} - {error.message}. "
            f"Method: {request.method}, Path: {request.path}, IP: {request.remote_addr}"
        )
        if error.status_code in [400, 422] and request.is_json:
            try:
                # Redact sensitive fields from logs (shallow redact for common keys)
                sensitive_keys = {
                    "password",
                    "current_password",
                    "new_password",
                    "token",
                    "secret",
                }
                redacted_data = {
                    k: ("[REDACTED]" if k.lower() in sensitive_keys else v)
                    for k, v in request.json.items()
                }
                log_message += f", Request Data: {redacted_data}"
            except Exception:
                log_message += ", Request Data: <unparseable JSON>"

        app.logger.warning(
            log_message, exc_info=True if error.status_code == 500 else False
        )
        response = error.to_dict()
        return jsonify(response), error.status_code

    @app.errorhandler(InfrastructureException)
    def handle_infrastructure_exception(error):
        app.logger.error(
            f"Infrastructure Exception: {error.status_code} - {error.error_code} - {error.message}. Method: {request.method}, Path: {request.path}, IP: {request.remote_addr}",
            exc_info=True,
        )
        response = error.to_dict()
        response["error_code"] = (
            "SERVICE_UNAVAILABLE"  # Override to ensure consistency with API contract for 503
        )
        return jsonify(response), error.status_code

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
