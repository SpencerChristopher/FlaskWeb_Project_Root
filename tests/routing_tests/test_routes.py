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

def test_blog_Article_not_found_returns_404(client):
    """Verifies the API correctly handles a resource not found within a valid route."""
    response = client.get('/api/blog/a-slug-that-is-not-real')
    assert response.status_code == 404
    assert response.content_type == 'application/json'
    data = response.get_json()
    assert data['error_code'] == 'NOT_FOUND'
    assert data['message'] == 'Article not found'

def test_admin_route_is_unauthorized_without_login(client):
    """Ensures the admin API endpoints are properly protected."""
    response = client.get('/api/content/articles')
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

# --- New Path-based Routing "Gate" Tests ---

def test_root_returns_spa_shell(client):
    """Verifies the root returns the SPA shell (base.html)."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data
    assert b'id="main-content"' in response.data

def test_catch_all_returns_spa_shell(client):
    """Verifies any non-API path returns the SPA shell (History API Support)."""
    # This should return base.html, NOT a 404.
    response = client.get('/admin/profile')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data
    assert b'id="main-content"' in response.data

def test_catch_all_blog_returns_spa_shell(client):
    """Verifies blog slugs return the SPA shell."""
    response = client.get('/blog/my-test-article')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data
