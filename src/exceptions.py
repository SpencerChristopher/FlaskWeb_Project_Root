class APIException(Exception):
    status_code = 500
    error_code = "INTERNAL_SERVER_ERROR"
    message = "An unexpected error occurred."

    def __init__(self, message=None, status_code=None, error_code=None, details=None):
        super().__init__(message)
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        if error_code:
            self.error_code = error_code
        self.details = details # For validation errors or more context

    def to_dict(self):
        rv = {
            "status_code": self.status_code,
            "error_code": self.error_code,
            "message": self.message
        }
        if self.details:
            rv["details"] = self.details
        return rv

class NotFoundException(APIException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found."

class UnauthorizedException(APIException):
    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Authentication required or invalid credentials."

class ForbiddenException(APIException):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "You do not have permission to access this resource."

class BadRequestException(APIException):
    status_code = 400
    error_code = "BAD_REQUEST"
    message = "The request was malformed or invalid."

class ValidationError(BadRequestException):
    error_code = "VALIDATION_ERROR"
    message = "Validation failed for the request data."
    # 'details' attribute will typically hold specific validation errors

class ConflictException(APIException):
    status_code = 409
    error_code = "CONFLICT"
    message = "Resource already exists or conflicts with an existing resource."
