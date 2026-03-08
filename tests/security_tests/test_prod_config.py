import os
import pytest


if os.environ.get("RUN_PROD_CONFIG_TESTS") != "1":
    pytest.skip(
        "Prod-config tests are opt-in. Set RUN_PROD_CONFIG_TESTS=1.",
        allow_module_level=True,
    )


def test_http_redirects_to_https_when_forced(client):
    response = client.get("/", base_url="http://localhost", follow_redirects=False)
    assert response.status_code in (301, 302)
    location = response.headers.get("Location", "")
    assert location.startswith("https://")


def test_hsts_present_on_https(client):
    response = client.get("/", base_url="https://localhost")
    assert "Strict-Transport-Security" in response.headers
