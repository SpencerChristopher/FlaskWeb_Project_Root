from flask.testing import FlaskClient


def test_login_sets_secure_cookies_and_omits_body_token(client: FlaskClient, setup_users):
    res = client.post(
        "/api/auth/login",
        json={"username": "testadmin", "password": "testpassword"},
    )

    assert res.status_code == 200

    set_cookie_headers = res.headers.getlist("Set-Cookie")
    assert any("access_token_cookie" in h and "HttpOnly" in h for h in set_cookie_headers)
    assert any("refresh_token_cookie" in h and "HttpOnly" in h for h in set_cookie_headers)
    assert any("csrf_access_token" in h for h in set_cookie_headers)

    json_data = res.get_json()
    assert "access_token" not in json_data
    assert "refresh_token" not in json_data
    assert json_data["message"] == "Login successful"
