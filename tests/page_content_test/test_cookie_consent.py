def test_cookie_consent_overlay_present(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'id="cookie-overlay"' in html
    assert 'id="cookie-banner"' in html
    assert 'id="cookie-accept"' in html
    assert 'id="cookie-decline"' in html
    assert 'id="manage-cookies"' in html


def test_cookie_consent_gates_admin_routes_in_spa_js(client):
    response = client.get("/static/app.js")
    assert response.status_code == 200
    js = response.data.decode("utf-8")

    assert "cookie_consent" in js
    assert "Consent Required" in js
