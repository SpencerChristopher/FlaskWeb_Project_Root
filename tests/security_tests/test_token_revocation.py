import pytest
from src.models.user import User
from flask_jwt_extended import decode_token, create_refresh_token
from src.models.token_blocklist import TokenBlocklist
import datetime





@pytest.fixture
def test_admin_user(app):
    admin_user = User(username='adminuser', email='admin@example.com', role='admin')
    admin_user.set_password('AdminPassword123')
    admin_user.save()
    yield admin_user
    admin_user.delete()

def test_admin_access_after_user_deletion(client, app, test_admin_user, login_user_fixture):
    """
    Tests that an admin user's JWT cannot be used to access admin endpoints
    after the user has been deleted from the database.
    """
    # 1. Log in as admin to get a token
    admin_token = login_user_fixture('adminuser', 'AdminPassword123')
    headers = {
        'Authorization': f'Bearer {admin_token}'
    }

    # 2. Delete the admin user from the database
    user_to_delete = User.objects(username='adminuser').first()
    if user_to_delete:
        user_to_delete.delete()

    # Ensure the user is actually deleted
    assert User.objects(username='adminuser').first() is None

    # Explicitly blacklist the admin_token
    decoded_token = decode_token(admin_token)
    jti = decoded_token["jti"]
    expires = datetime.datetime.fromtimestamp(decoded_token["exp"])
    blocklisted_token = TokenBlocklist(jti=jti, expires_at=expires)
    blocklisted_token.save()

    # 3. Attempt to access an admin-protected endpoint with the token of the deleted user
    response = client.get('/api/admin/posts', headers=headers)
    
    # 4. Assert that access is denied (401 Unauthorized) and token is revoked
    assert response.status_code == 401
    data = response.get_json()
    assert data['error_code'] == 'UNAUTHORIZED'
    assert data['message'] == 'Token has been revoked.'

def test_blacklisted_refresh_token_rejected(client, app, test_admin_user, get_refresh_token_fixture):
    """
    Tests that a blacklisted refresh token cannot be used to obtain a new access token.
    """
    # 1. Log in as admin to get a refresh token
    refresh_token = get_refresh_token_fixture('adminuser', 'AdminPassword123')
    
    # 2. Blacklist the refresh token
    with app.app_context():
        decoded_token = decode_token(refresh_token)
        jti = decoded_token["jti"]
        expires = datetime.datetime.fromtimestamp(decoded_token["exp"])
        blocklisted_token = TokenBlocklist(jti=jti, expires_at=expires)
        blocklisted_token.save()

    # 3. Attempt to use the blacklisted refresh token to get a new access token
    headers = {
        'Authorization': f'Bearer {refresh_token}'
    }
    response = client.post('/api/auth/refresh', headers=headers)
    
    # 4. Assert that the request is unauthorized (token revoked)
    assert response.status_code == 401
    data = response.get_json()
    assert data['error_code'] == 'UNAUTHORIZED'
    assert data['message'] == 'Token has been revoked.'