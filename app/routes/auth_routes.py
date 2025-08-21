from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from app.models.user import User

bp = Blueprint('auth_routes', __name__, url_prefix='/api/auth')

login_manager = LoginManager()
# Note: For a pure API, instead of a login_view, you should configure
# the login_manager to return a 401 error. This is typically done in
# the main app factory like so:
#
# @login_manager.unauthorized_handler
# def unauthorized():
#     return jsonify({'error': 'Authentication required'}), 401
#
# Since we cannot edit the app factory here, this line is removed.
# login_manager.login_view = 'auth_routes.login'

@login_manager.user_loader
def load_user(user_id):
    return User.find_by_id(current_app.db, user_id)

@bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'message': 'User already logged in', 'user': {'username': current_user.username}}), 200

    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    username = data.get('username')
    password = data.get('password')

    user = User.find_by_username(current_app.db, username)
    if user and user.check_password(password):
        login_user(user)
        return jsonify({'message': 'Logged in successfully', 'user': {'username': user.username}}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@bp.route('/status', methods=['GET'])
def status():
    if current_user.is_authenticated:
        return jsonify({
            'logged_in': True,
            'user': {'username': current_user.username, 'id': current_user.get_id()}
        }), 200
    else:
        return jsonify({'logged_in': False}), 200
