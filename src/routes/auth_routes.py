"""
This module defines the API routes for user authentication.

It includes routes for logging in, logging out, and checking the
current authentication status.
"""

import datetime
from flask import Blueprint, request, jsonify, Response, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
    decode_token,
    get_jwt,
)
from typing import Dict, Any
from src.events import dispatch_event, user_logged_in
from src.extensions import limiter
from src.exceptions import BadRequestException, UnauthorizedException
from src.schemas import UserRegistration, ChangePasswordRequest
from src.services import get_auth_service


bp = Blueprint('auth_routes', __name__, url_prefix='/api/auth')
auth_service = get_auth_service()

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

    current_app.logger.debug(f"Login attempt for username: '{username}'")

    try:
        user = auth_service.authenticate(username, password)
    except UnauthorizedException:
        current_app.logger.warning(
            f"Failed login attempt for user: {username} from IP: {request.remote_addr}"
        )
        raise

    token_claims = auth_service.build_token_claims(user)
    access_token = create_access_token(
        identity=str(user.id), additional_claims=token_claims
    )
    refresh_token = create_refresh_token(
        identity=str(user.id), additional_claims=token_claims
    )

    # Phase 3: Record active session in Redis
    refresh_jti = decode_token(refresh_token)["jti"]
    refresh_ttl = current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
    auth_service._session_service.set_active_refresh_token(
        user_id=str(user.id),
        jti=refresh_jti,
        ttl_seconds=int(refresh_ttl.total_seconds())
    )

    dispatch_event(user_logged_in, current_app._get_current_object(), user_id=str(user.id))
    current_app.logger.info(f"Successful login for user: {username} from IP: {request.remote_addr}")

    response = jsonify({
        'message': 'Login successful'
    })
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response, 200

@bp.route('/register', methods=['POST'])
def register() -> Response:
    """
    Registers a new user.
    """
    user_data = UserRegistration(**request.get_json())

    # Placeholder for actual user registration logic
    current_app.logger.info(f"New user registration for: {user_data.username} from IP: {request.remote_addr}")
    return jsonify({'message': 'User registration endpoint (placeholder)', 'received_data': user_data.model_dump()}), 200


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout() -> Response:
    """
    Logs out the currently authenticated user and invalidates their session.
    """
    # Phase 3: Invalidate active session in Redis
    current_user_id = get_jwt_identity()
    if current_user_id:
        auth_service._session_service.invalidate_session(current_user_id)

    jwt_payload = get_jwt()
    jti = jwt_payload["jti"]
    # Block for access token expiry (typically 15 minutes)
    expires_at = datetime.datetime.fromtimestamp(jwt_payload["exp"], datetime.timezone.utc)
    auth_service.revoke_token(jti, expires_at)

    response = jsonify({'message': 'Logged out successfully'})
    unset_jwt_cookies(response)
    return response, 200

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh() -> Response:
    """
    Refreshes an access token using a valid refresh token.
    Validates the token's JTI against the active session in Redis.
    """
    current_user_id = get_jwt_identity()
    refresh_jti = get_jwt()["jti"]

    # Phase 3: Enforce session validity
    if not auth_service._session_service.is_refresh_token_valid(current_user_id, refresh_jti):
        current_app.logger.warning(
            f"Invalid refresh attempt for user ID: {current_user_id} with JTI: {refresh_jti}. "
            "Session likely invalidated by a newer login."
        )
        raise UnauthorizedException("Session has expired or been invalidated")

    current_app.logger.info(f"Token refreshed for user ID: {current_user_id} from IP: {request.remote_addr}")
    user = auth_service.get_user_or_raise(current_user_id)
    new_access_token = create_access_token(
        identity=current_user_id,
        additional_claims=auth_service.build_token_claims(user)
    )
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
        user = auth_service.get_user(current_user_id)
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
    data = ChangePasswordRequest(**request.get_json())
    user_id = get_jwt_identity()
    auth_service.change_password(
        user_id=user_id,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    current_app.logger.info(f"Password successfully changed for user ID: {user_id} from IP: {request.remote_addr}")

    return jsonify({'message': 'Password updated successfully'}), 200
