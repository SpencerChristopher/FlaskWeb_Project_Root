import pytest
from src.models.user import User

class TestTokenLifecycle:
    def test_successful_admin_login(self, client, setup_users):
        admin_user, _ = setup_users
        response = client.post('/api/auth/login', json={'username': 'testadmin', 'password': 'testpassword'})
        assert response.status_code == 200
        assert response.json['message'] == 'Login successful'

    def test_failed_login_invalid_password(self, client, setup_users):
        response = client.post('/api/auth/login', json={'username': 'testadmin', 'password': 'wrongpassword'})
        assert response.status_code == 401

    def test_failed_login_non_existent_user(self, client, setup_users):
        response = client.post('/api/auth/login', json={'username': 'noone', 'password': 'password'})
        assert response.status_code == 401

    def test_logout_successful(self, client, setup_users, login_user_fixture):
        token = login_user_fixture('testadmin', 'testpassword')
        headers = {'Authorization': f'Bearer {token}'}
        response = client.post('/api/auth/logout', headers=headers)
        assert response.status_code == 200

    def test_refresh_access_token_successful(self, client, setup_users, get_refresh_token_fixture):
        refresh_token = get_refresh_token_fixture('testadmin', 'testpassword')
        headers = {'Authorization': f'Bearer {refresh_token}'}
        response = client.post('/api/auth/refresh', headers=headers)
        assert response.status_code == 200
        assert response.json['message'] == 'Token refreshed'
