"""
This module defines the API routes for user authentication.

It includes routes for logging in, logging out, and checking the
current authentication status.
"""

from flask import Blueprint, request, jsonify, Response, current_app
from flask_jwt_extended import create_access_token, jwt_required,     get_jwt_identity, create_refresh_token, set_access_cookies, set_refresh_cookies, unset_jwt_cookies
from src.models.user import User
from typing import Dict, Any
from src.events import user_logged_in
from src.extensions import limiter # Import limiter
from src.exceptions import BadRequestException, UnauthorizedException
from src.schemas import UserRegistration, ChangePasswordRequest
from pydantic import ValidationError as PydanticValidationError


bp = Blueprint('auth_routes', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute") # Apply rate limit
def login() -> Response:
    """
    Authenticates a user and returns JWT access and refresh tokens.
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
        refresh_token = create_refresh_token(
            identity=str(user.id)
        )

        user_logged_in.send(current_app._get_current_object(), user_id=str(user.id))
        current_app.logger.info(f"Successful login for user: {username} from IP: {request.remote_addr}")

        response = jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token
        })
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response, 200
    else:
        current_app.logger.warning(f"Failed login attempt for user: {username} from IP: {request.remote_addr}")
        raise UnauthorizedException("Invalid username or password")

@bp.route('/register', methods=['POST'])
def register() -> Response:
    """
    Registers a new user.
    """
    try:
        user_data = UserRegistration(**request.get_json())
    except PydanticValidationError as e:
        # Extract just the messages for a cleaner response
        error_messages = [error['msg'] for error in e.errors()]
        raise BadRequestException("Invalid registration data", details=error_messages)

    # Placeholder for actual user registration logic
    current_app.logger.info(f"New user registration for: {user_data.username} from IP: {request.remote_addr}")
    return jsonify({'message': 'User registration endpoint (placeholder)', 'received_data': user_data.model_dump()}), 200


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout() -> Response:
    """
    Logs out the currently authenticated user.
    """
    response = jsonify({'message': 'Logged out successfully'})
    unset_jwt_cookies(response)
    return response, 200

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh() -> Response:
    """
    Refreshes an access token using a valid refresh token.
    """
    current_user_id = get_jwt_identity()
    current_app.logger.info(f"Token refreshed for user ID: {current_user_id} from IP: {request.remote_addr}")
    new_access_token = create_access_token(identity=current_user_id)
    response = jsonify({'message': 'Token refreshed'})
    set_access_cookies(response, new_access_token)
    return response, 200


@bp.route('/status', methods=['GET'])
@jwt_required(optional=True)
def status() -> Response:
    """
    Checks the authentication status of the current session.
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

@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password() -> Response:
    """
    Allows a logged-in user to change their password.
    """
    try:
        data = ChangePasswordRequest(**request.get_json())
    except PydanticValidationError as e:
        # Extract just the messages for a cleaner response
        error_messages = [error['msg'] for error in e.errors()]
        raise BadRequestException("Invalid data", details=error_messages)

    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user or not user.check_password(data.current_password):
        raise UnauthorizedException("Invalid current password")

    user.set_password(data.new_password)
    user.save()
    current_app.logger.info(f"Password successfully changed for user ID: {user_id} from IP: {request.remote_addr}")

    return jsonify({'message': 'Password updated successfully'}), 200