import os

def test_security_headers_present(client):
    response = client.get("/")

    assert "Content-Security-Policy" in response.headers
    assert "Referrer-Policy" in response.headers
    assert "Permissions-Policy" in response.headers
    
    # HSTS is only added by Talisman when FLASK_ENV is production
    if os.environ.get("FLASK_ENV") == "production":
        assert "Strict-Transport-Security" in response.headers
