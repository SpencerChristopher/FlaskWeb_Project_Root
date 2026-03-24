import pytest

from src.exceptions import InfrastructureException
from src.services.email_service import EmailService


class _DummySMTP:
    def __init__(self, *args, **kwargs):
        self.started_tls = False
        self.logged_in = False
        self.sent_messages = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, *_args, **_kwargs):
        self.logged_in = True

    def send_message(self, message):
        self.sent_messages.append(message)


def test_email_service_sends_contact_message(monkeypatch):
    dummy_smtp = _DummySMTP()

    def fake_smtp(*_args, **_kwargs):
        return dummy_smtp

    monkeypatch.setattr("src.services.email_service.smtplib.SMTP", fake_smtp)

    service = EmailService(
        host="smtp.test",
        port=587,
        username="user",
        password="pass",
        use_tls=True,
        use_ssl=False,
        from_email="info@example.com",
        to_email="contact@example.com",
    )
    service.send_contact_email(
        name="Chris",
        email="chris@example.com",
        message="Hello",
        remote_ip="127.0.0.1",
        user_agent="pytest",
    )

    assert dummy_smtp.started_tls is True
    assert dummy_smtp.logged_in is True
    assert len(dummy_smtp.sent_messages) == 1


def test_email_service_raises_on_failure(monkeypatch):
    class _FailSMTP(_DummySMTP):
        def send_message(self, _message):
            raise RuntimeError("smtp down")

    def fake_smtp(*_args, **_kwargs):
        return _FailSMTP()

    monkeypatch.setattr("src.services.email_service.smtplib.SMTP", fake_smtp)

    service = EmailService(
        host="smtp.test",
        port=587,
        username="user",
        password="pass",
        use_tls=False,
        use_ssl=False,
        from_email="info@example.com",
        to_email="contact@example.com",
    )

    with pytest.raises(InfrastructureException):
        service.send_contact_email(
            name="Chris",
            email="chris@example.com",
            message="Hello",
        )
