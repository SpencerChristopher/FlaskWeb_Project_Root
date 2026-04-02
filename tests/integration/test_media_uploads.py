import pytest
import io
from PIL import Image


@pytest.fixture
def admin_headers(setup_users, login_user_fixture):
    token = login_user_fixture("testadmin", "testpassword")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(setup_users, login_user_fixture):
    token = login_user_fixture("testuser", "testpassword")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.heavy
def test_upload_image_success(client, admin_headers):
    image_bytes = io.BytesIO()
    Image.new("RGB", (1, 1), color=(255, 255, 255)).save(image_bytes, format="JPEG")
    image_bytes.seek(0)
    data = {"file": (image_bytes, "test.jpg")}
    resp = client.post(
        "/api/content/media",
        data=data,
        content_type="multipart/form-data",
        headers=admin_headers,
    )
    assert resp.status_code == 201
    json_data = resp.get_json()
    assert "url" in json_data

    # Cleanup: Delete the uploaded image
    url = json_data["url"]
    del_resp = client.delete(f"/api/content/media?url={url}", headers=admin_headers)
    assert del_resp.status_code == 200


@pytest.mark.heavy
def test_upload_invalid_extension(client, admin_headers):
    data = {"file": (io.BytesIO(b"<?php phpinfo(); ?>"), "malicious.php")}
    resp = client.post(
        "/api/content/media",
        data=data,
        content_type="multipart/form-data",
        headers=admin_headers,
    )
    assert resp.status_code == 400


@pytest.mark.heavy
def test_member_cannot_upload(client, user_headers):
    data = {"file": (io.BytesIO(b"fake content"), "test.jpg")}
    resp = client.post(
        "/api/content/media",
        data=data,
        content_type="multipart/form-data",
        headers=user_headers,
    )
    assert resp.status_code == 403
