import pytest
import io
from tests.security_tests.conftest import admin_headers, admin_user, regular_user, user_headers

@pytest.mark.heavy
def test_upload_image_success(client, admin_headers):
    """Admin can upload a valid image."""
    data = {
        'file': (io.BytesIO(b"fake image content"), 'test.jpg')
    }
    resp = client.post(
        "/api/content/media",
        data=data,
        content_type='multipart/form-data',
        headers=admin_headers
    )
    assert resp.status_code == 201
    json_data = resp.get_json()
    assert "url" in json_data
    assert json_data["url"].startswith("/static/uploads/")

@pytest.mark.heavy
def test_upload_invalid_extension(client, admin_headers):
    """Admin cannot upload a script file."""
    data = {
        'file': (io.BytesIO(b"<?php phpinfo(); ?>"), 'malicious.php')
    }
    resp = client.post(
        "/api/content/media",
        data=data,
        content_type='multipart/form-data',
        headers=admin_headers
    )
    assert resp.status_code == 400
    assert "Unsupported file extension" in resp.get_json()["message"]

@pytest.mark.heavy
def test_member_cannot_upload(client, user_headers):
    """Regular members cannot upload media."""
    data = {
        'file': (io.BytesIO(b"fake content"), 'test.jpg')
    }
    resp = client.post(
        "/api/content/media",
        data=data,
        content_type='multipart/form-data',
        headers=user_headers
    )
    assert resp.status_code == 403
