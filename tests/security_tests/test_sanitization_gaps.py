import pytest
from werkzeug.datastructures import FileStorage
from io import BytesIO

def test_register_does_not_leak_password(client):
    """
    Vulnerability Check: Ensure registration does not echo the password back.
    """
    payload = {
        "username": "security_test_user",
        "email": "security@example.com",
        "password": "VERY_SECRET_PASSWORD_123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    
    data = response.get_json()
    assert "password" not in data, "CRITICAL: Password leaked in registration response!"
    assert data["username"] == "security_test_user"

def test_media_upload_path_traversal_protection(client, admin_headers):
    """
    Vulnerability Check: Ensure filenames are sanitized to prevent path traversal.
    """
    data = {
        'file': (BytesIO(b"dummy content"), "../../../../tmp/evil.png")
    }
    response = client.post(
        "/api/content/media",
        data=data,
        content_type='multipart/form-data',
        headers=admin_headers
    )
    
    assert response.status_code == 201
    url = response.get_json()["url"]
    assert ".." not in url, f"Path traversal characters found in returned URL: {url}"
    assert "/static/uploads/" in url
