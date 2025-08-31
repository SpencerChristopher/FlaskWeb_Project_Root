import json

def test_home_api_returns_json(client):
    """Verifies the main public API endpoint (/api/home) is working."""
    response = client.get('/api/home')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    data = response.get_json()
    assert 'title' in data

def test_non_existent_api_route_returns_404(client):
    """Verifies that the JSON-based 404 error handler is working correctly."""
    response = client.get('/api/i-do-not-exist')
    assert response.status_code == 404
    assert response.content_type == 'application/json'
    data = response.json
    assert data['error_code'] == 'NOT_FOUND'
    assert data['message'] == 'The requested URL was not found on the server.'

def test_blog_post_not_found_returns_404(client):
    """Verifies the API correctly handles a resource not found within a valid route."""
    response = client.get('/api/blog/a-slug-that-is-not-real')
    assert response.status_code == 404
    assert response.content_type == 'application/json'
    data = response.get_json()
    assert data['error_code'] == 'NOT_FOUND'
    assert data['message'] == 'Post not found'

def test_admin_route_is_unauthorized_without_login(client):
    """Ensures the admin API endpoints are properly protected."""
    response = client.get('/api/admin/posts')
    assert response.status_code == 401
    assert response.content_type == 'application/json'
    data = response.get_json()
    assert data['error_code'] == 'UNAUTHORIZED'
    assert data['message'] == 'Missing or invalid token.'

def test_change_password_route_is_unauthorized_without_login(client):
    """Ensures the change password API endpoint is properly protected."""
    response = client.post('/api/auth/change-password', json={
        "current_password": "old",
        "new_password": "new"
    })
    assert response.status_code == 401
    assert response.content_type == 'application/json'
    data = response.get_json()
    assert data['error_code'] == 'UNAUTHORIZED'
    assert data['message'] == 'Missing or invalid token.'
