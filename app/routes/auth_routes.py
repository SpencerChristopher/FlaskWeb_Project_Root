"""
This module defines the API routes for user authentication.

It includes routes for logging in, logging out, and checking the
current authentication status.
"""

from flask import Blueprint, request, jsonify, current_app, Response
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from app.models.user import User
from typing import Dict, Any

bp = Blueprint('auth_routes', __name__, url_prefix='/api/auth')

# Initialize the LoginManager for the application
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id: str) -> User:
    """
    Loads a user from the database given their ID.
    This function is required by Flask-Login to manage user sessions.

    Args:
        user_id (str): The ID of the user to load.

    Returns:
        User: The User object if found, otherwise None.
    """
    return User.find_by_id(current_app.db, user_id)

@bp.route('/login', methods=['POST'])
def login() -> Response:
    """
    Authenticates a user and establishes a session.

    Expects a JSON payload with:
    - 'username' (str)
    - 'password' (str)

    Returns:
        Response: A success message and user info, or an error message.
    """
    if current_user.is_authenticated:
        return jsonify({
            'message': 'User already logged in',
            'user': {'username': current_user.username}
        }), 200

    data: Dict[str, Any] = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    user = User.find_by_username(current_app.db, username)
    if user and user.check_password(password):
        login_user(user)
        return jsonify({
            'message': 'Logged in successfully',
            'user': {'username': user.username}
        }), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@bp.route('/logout', methods=['POST'])
@login_required
def logout() -> Response:
    """
    Logs out the currently authenticated user and clears the session.

    Returns:
        Response: A success message.
    """
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@bp.route('/status', methods=['GET'])
def status() -> Response:
    """
    Checks the authentication status of the current session.

    This is useful for the frontend to determine if a user is logged in
    on application startup.

    Returns:
        Response: A JSON object indicating login status and user info.
    """
    if current_user.is_authenticated:
        return jsonify({
            'logged_in': True,
            'user': {'username': current_user.username, 'id': current_user.get_id()}
        }), 200
    else:
        return jsonify({'logged_in': False}), 200
