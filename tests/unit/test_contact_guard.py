import pytest

from src.services.contact_guard import ContactGuard
from src.exceptions import BadRequestException


def test_contact_guard_rejects_honeypot():
    guard = ContactGuard()
    payload = {"name": "Bot", "website": "spam"}
    with pytest.raises(BadRequestException):
        guard.validate(payload)


def test_contact_guard_rejects_too_fast_submission():
    guard = ContactGuard(min_time_ms=1500, time_provider=lambda: 2.0)
    payload = {"form_loaded_at": 1000}  # 1s after epoch in ms
    with pytest.raises(BadRequestException):
        guard.validate(payload)


def test_contact_guard_allows_valid_timing():
    guard = ContactGuard(min_time_ms=1500, time_provider=lambda: 3.0)
    payload = {"form_loaded_at": 1000}
    guard.validate(payload)
