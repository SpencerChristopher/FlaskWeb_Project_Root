import pytest
from src.models.user import User

# Fixture to create a user in the database
@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(username='testuser', email='test@example.com', role='user')
        user.set_password('Password123') # Complex password
        user.save()
        yield user
        user.delete()

# Helper function to log in a user and get tokens
def login_user(client, username, password):
    response = client.post('/api/auth/login', json={
        'username': username,
        'password': password
    })
    assert response.status_code == 200
    return response.get_json()['access_token']

def test_change_password_successfully(client, test_user):
    """Tests that a logged-in user can successfully change their password."""
    # 1. Login to get a token
    token = login_user(client, 'testuser', 'Password123')
    headers = {
        'Authorization': f'Bearer {token}'
    }

    # 2. Change the password
    response = client.post('/api/auth/change-password', json={
        'current_password': 'Password123',
        'new_password': 'NewPassword456' # Complex password
    }, headers=headers)
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Password updated successfully'

    # 3. Verify the old password no longer works
    login_response_old = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'Password123'
    })
    assert login_response_old.status_code == 401

    # 4. Verify the new password works
    login_response_new = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'NewPassword456'
    })
    assert login_response_new.status_code == 200

def test_change_password_with_wrong_current_password(client, test_user):
    """Tests that changing password fails with an incorrect current password."""
    token = login_user(client, 'testuser', 'Password123')
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = client.post('/api/auth/change-password', json={
        'current_password': 'wrongpassword',
        'new_password': 'NewPassword456' # Complex password
    }, headers=headers)
    assert response.status_code == 401
    data = response.get_json()
    assert data['error_code'] == 'UNAUTHORIZED'
    assert data['message'] == 'Invalid current password'

def test_change_password_with_missing_data(client, test_user):
    """Tests that changing password fails if required fields are missing."""
    token = login_user(client, 'testuser', 'Password123')
    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Missing new_password
    response = client.post('/api/auth/change-password', json={
        'current_password': 'Password123'
    }, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data['error_code'] == 'BAD_REQUEST'
    assert data['message'] == 'Invalid data'
    # Check that the details list contains a message about the missing field
    assert any('Field required' in detail for detail in data['details'])
