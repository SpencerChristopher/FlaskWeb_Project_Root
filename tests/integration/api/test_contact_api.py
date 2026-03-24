import time

import pytest

from src.exceptions import InfrastructureException


class _DummyTurnstile:
    def __init__(self, enabled=True, result=True):
        self.enabled = enabled
        self.result = result
        self.calls = []

    def verify_token(self, token, remote_ip=None):
        self.calls.append((token, remote_ip))
        return self.result


class _DummyEmail:
    def __init__(self, should_fail=False):
        self.sent = []
        self.should_fail = should_fail

    def send_contact_email(self, name, email, message, remote_ip=None, user_agent=None):
        if self.should_fail:
            raise InfrastructureException("SMTP down")
        self.sent.append(
            {
                "name": name,
                "email": email,
                "message": message,
                "remote_ip": remote_ip,
                "user_agent": user_agent,
            }
        )


def _payload():
    return {
        "name": "Chris",
        "email": "chris@example.com",
        "message": "Hello",
        "turnstile_token": "token",
        "form_loaded_at": int(time.time() * 1000) - 5000,
    }


def test_contact_success(client, monkeypatch):
    from src.routes import api_routes

    dummy_turnstile = _DummyTurnstile(enabled=True, result=True)
    dummy_email = _DummyEmail()
    monkeypatch.setattr(api_routes, "turnstile_service", dummy_turnstile)
    monkeypatch.setattr(api_routes, "email_service", dummy_email)

    response = client.post("/api/contact", json=_payload())
    assert response.status_code == 200
    assert dummy_email.sent


def test_contact_missing_turnstile_token(client, monkeypatch):
    from src.routes import api_routes

    dummy_turnstile = _DummyTurnstile(enabled=True, result=True)
    dummy_email = _DummyEmail()
    monkeypatch.setattr(api_routes, "turnstile_service", dummy_turnstile)
    monkeypatch.setattr(api_routes, "email_service", dummy_email)

    payload = _payload()
    payload.pop("turnstile_token")
    response = client.post("/api/contact", json=payload)
    assert response.status_code == 400


def test_contact_turnstile_failure(client, monkeypatch):
    from src.routes import api_routes

    dummy_turnstile = _DummyTurnstile(enabled=True, result=False)
    dummy_email = _DummyEmail()
    monkeypatch.setattr(api_routes, "turnstile_service", dummy_turnstile)
    monkeypatch.setattr(api_routes, "email_service", dummy_email)

    response = client.post("/api/contact", json=_payload())
    assert response.status_code == 400


def test_contact_turnstile_disabled_allows_missing_token(client, monkeypatch):
    from src.routes import api_routes

    dummy_turnstile = _DummyTurnstile(enabled=False, result=False)
    dummy_email = _DummyEmail()
    monkeypatch.setattr(api_routes, "turnstile_service", dummy_turnstile)
    monkeypatch.setattr(api_routes, "email_service", dummy_email)

    payload = _payload()
    payload.pop("turnstile_token")
    response = client.post("/api/contact", json=payload)
    assert response.status_code == 200


def test_contact_rejects_honeypot(client, monkeypatch):
    from src.routes import api_routes

    dummy_turnstile = _DummyTurnstile(enabled=True, result=True)
    dummy_email = _DummyEmail()
    monkeypatch.setattr(api_routes, "turnstile_service", dummy_turnstile)
    monkeypatch.setattr(api_routes, "email_service", dummy_email)

    payload = _payload()
    payload["website"] = "spam"
    response = client.post("/api/contact", json=payload)
    assert response.status_code == 400


def test_contact_rejects_too_fast(client, monkeypatch):
    from src.routes import api_routes

    dummy_turnstile = _DummyTurnstile(enabled=True, result=True)
    dummy_email = _DummyEmail()
    monkeypatch.setattr(api_routes, "turnstile_service", dummy_turnstile)
    monkeypatch.setattr(api_routes, "email_service", dummy_email)

    payload = _payload()
    payload["form_loaded_at"] = int(time.time() * 1000)
    response = client.post("/api/contact", json=payload)
    assert response.status_code == 400


def test_contact_handles_email_failure(client, monkeypatch):
    from src.routes import api_routes

    dummy_turnstile = _DummyTurnstile(enabled=True, result=True)
    dummy_email = _DummyEmail(should_fail=True)
    monkeypatch.setattr(api_routes, "turnstile_service", dummy_turnstile)
    monkeypatch.setattr(api_routes, "email_service", dummy_email)

    response = client.post("/api/contact", json=_payload())
    assert response.status_code == 503
