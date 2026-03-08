from flask.testing import FlaskClient


def test_protected_endpoint_fails_without_csrf(client: FlaskClient, setup_users):
    client.post(
        "/api/auth/login",
        json={"username": "testadmin", "password": "testpassword"},
    )

    res = client.post("/api/auth/logout")

    assert res.status_code == 401
    assert res.get_json()["message"] == "Missing or invalid token."


def test_protected_endpoint_succeeds_with_csrf(client: FlaskClient, setup_users):
    login_res = client.post(
        "/api/auth/login",
        json={"username": "testadmin", "password": "testpassword"},
    )

    csrf_token = None
    csrf_path_is_root = False
    for cookie in login_res.headers.getlist("Set-Cookie"):
        if "csrf_access_token" in cookie:
            csrf_token = cookie.split("=")[1].split(";")[0]
            # Check specifically for Path=/ and NOT Path=/api/
            if "Path=/" in cookie and "Path=/api/" not in cookie:
                csrf_path_is_root = True
            break

    assert csrf_token is not None, "CSRF token not found in login response cookies"
    assert (
        csrf_path_is_root
    ), f"CSRF cookie path must be root ('/'). Found cookie: {cookie}"

    headers = {"X-CSRF-TOKEN": csrf_token}
    res = client.post("/api/auth/logout", headers=headers)

    assert res.status_code == 200
    assert res.get_json()["message"] == "Logged out successfully"
