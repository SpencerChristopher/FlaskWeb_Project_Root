def test_security_headers_present(client):
    response = client.get("/", base_url="https://localhost")

    assert "Content-Security-Policy" in response.headers
    assert "Strict-Transport-Security" in response.headers
    assert "Referrer-Policy" in response.headers
    assert "Permissions-Policy" in response.headers
