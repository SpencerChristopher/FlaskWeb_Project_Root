import pytest
from werkzeug.datastructures import FileStorage
from io import BytesIO
from PIL import Image

def test_register_restricted_to_admin(client, admin_headers):
    """
    Ensure registration is restricted to users with users:manage permission (Admin).
    """
    payload = {
        "username": "new_member",
        "email": "member@example.com",
        "password": "Password123!"
    }
    # 1. Authorized Attempt (Admin)
    response = client.post("/api/auth/register", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert "password" not in data
    assert data["user"]["username"] == "new_member"

def test_register_blocked_for_anonymous(client):
    """
    Ensure anonymous users cannot access the registration endpoint.
    """
    payload = {"username": "spy", "email": "spy@bad.com", "password": "123"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 401

def test_media_upload_path_traversal_protection(client, admin_headers):
    """
    Vulnerability Check: Ensure filenames are sanitized to prevent path traversal.
    """
    image_bytes = BytesIO()
    Image.new("RGB", (1, 1), color=(255, 255, 255)).save(image_bytes, format="PNG")
    image_bytes.seek(0)
    data = {
        'file': (image_bytes, "../../../../tmp/evil.png")
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
