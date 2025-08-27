
"""
This module defines the API routes for user authentication.

It includes routes for logging in, logging out, and checking the
current authentication status.
"""

from flask import Blueprint, request, jsonify, Response, current_app
from flask_jwt_extended import create_access_token, jwt_required,     get_jwt_identity
from src.models.user import User
from typing import Dict, Any
from src.events import user_logged_in
from src.extensions import limiter # Import limiter
from src.exceptions import BadRequestException, UnauthorizedException
from src.schemas import UserRegistration
from pydantic import ValidationError as PydanticValidationError


bp = Blueprint('auth_routes', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute") # Apply rate limit
def login() -> Response:
    """
    Authenticates a user and returns JWT access and refresh tokens.

    Expects a JSON payload with:
    - 'username' (str)
    - 'password' (str)

    Returns:
        Response: A JSON object with access and refresh tokens, or an error
        message.
    """
    data: Dict[str, Any] = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        raise BadRequestException("Username and password are required")

    username = data['username']
    password = data['password']

    user = User.objects(username=username).first()
    if user and user.check_password(password):
        access_token = create_access_token(
            identity=str(user.id), additional_claims={"roles": [user.role]}
        )
        refresh_token = create_access_token(
            identity=str(user.id), fresh=False
        )  # Refresh tokens are not "fresh"

        user_logged_in.send(current_app._get_current_object(), user_id=str(user.id))

        return jsonify(access_token=access_token, refresh_token=refresh_token), 200
    else:
        raise UnauthorizedException("Invalid username or password")

@bp.route('/register', methods=['POST'])
def register() -> Response:
    """
    Registers a new user.
    """
    try:
        user_data = UserRegistration(**request.get_json())
    except PydanticValidationError as e:
        raise BadRequestException("Invalid registration data", details=e.errors())

    # Placeholder for actual user registration logic
    # In a real app, you would check if username/email already exists
    # and then create the user.
    return jsonify({'message': 'User registration endpoint (placeholder)', 'received_data': user_data.model_dump()}), 200


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout() -> Response:
    """
    Logs out the currently authenticated user by invalidating their token.
    (Note: This example does not implement token blocklisting/revocation,
    which is recommended for production.)

    Returns:
        Response: A success message.
    """
    # Token blocklisting/revocation logic would go here in a real app
    return jsonify({'message': 'Logged out successfully'}), 200


@bp.route('/status', methods=['GET'])
@jwt_required(optional=True)
def status() -> Response:
    """
    Checks the authentication status of the current session using JWT.

    Returns:
        Response: A JSON object indicating login status and user info from JWT.
    """
    current_user_id = get_jwt_identity()
    if current_user_id:
        user = User.objects(id=current_user_id).first()
        if user:
            return jsonify({
                'logged_in': True,
                'user': {
                    'username': user.username,
                    'id': str(user.id),
                    'role': user.role
                }
            }), 200
    return jsonify({'logged_in': False}), 200
