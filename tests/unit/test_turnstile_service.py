import pytest

from src.services.turnstile_service import TurnstileService


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_turnstile_disabled_skips_verification(monkeypatch):
    service = TurnstileService(secret_key="dummy", enabled=False)
    called = {"value": False}

    def fake_post(*_args, **_kwargs):
        called["value"] = True
        return _FakeResponse({"success": True})

    monkeypatch.setattr("src.services.turnstile_service.requests.post", fake_post)
    assert service.verify_token("token") is True
    assert called["value"] is False


def test_turnstile_success_returns_true(monkeypatch):
    service = TurnstileService(secret_key="dummy", enabled=True)

    def fake_post(*_args, **_kwargs):
        return _FakeResponse({"success": True})

    monkeypatch.setattr("src.services.turnstile_service.requests.post", fake_post)
    assert service.verify_token("token") is True


def test_turnstile_failure_returns_false(monkeypatch):
    service = TurnstileService(secret_key="dummy", enabled=True)

    def fake_post(*_args, **_kwargs):
        return _FakeResponse({"success": False})

    monkeypatch.setattr("src.services.turnstile_service.requests.post", fake_post)
    assert service.verify_token("token") is False


def test_turnstile_network_error_fails_closed(monkeypatch):
    service = TurnstileService(secret_key="dummy", enabled=True)

    def fake_post(*_args, **_kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("src.services.turnstile_service.requests.post", fake_post)
    assert service.verify_token("token") is False


@pytest.mark.parametrize("token", [None, ""])
def test_turnstile_missing_token_fails(token):
    service = TurnstileService(secret_key="dummy", enabled=True)
    assert service.verify_token(token) is False
