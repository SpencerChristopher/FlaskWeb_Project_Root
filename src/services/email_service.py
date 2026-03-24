"""
SMTP-backed email delivery service.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from src.exceptions import InfrastructureException, BadRequestException

logger = logging.getLogger(__name__)


class EmailService:
    """Send transactional emails via SMTP.

    Args:
        host: SMTP host.
        port: SMTP port.
        username: SMTP username.
        password: SMTP password.
        use_tls: Whether to issue STARTTLS.
        use_ssl: Whether to use SMTPS.
        from_email: Sender address.
        to_email: Recipient address.
    """

    def __init__(
        self,
        *,
        host: str | None,
        port: int,
        username: str | None,
        password: str | None,
        use_tls: bool,
        use_ssl: bool,
        from_email: str | None,
        to_email: str | None,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._use_ssl = use_ssl
        self._from_email = from_email
        self._to_email = to_email

    def _validate_header_value(self, value: str, label: str) -> None:
        if "\n" in value or "\r" in value:
            raise BadRequestException(f"Invalid {label} header.")

    def send_contact_email(
        self,
        *,
        name: str,
        email: str,
        message: str,
        remote_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Send a contact form submission via SMTP."""
        if not self._host or not self._from_email or not self._to_email:
            raise InfrastructureException("SMTP is not configured.")

        self._validate_header_value(name, "name")
        self._validate_header_value(email, "email")

        subject = f"Contact form submission from {name}"
        body_lines = [
            f"Name: {name}",
            f"Email: {email}",
        ]
        if remote_ip:
            body_lines.append(f"IP: {remote_ip}")
        if user_agent:
            body_lines.append(f"User Agent: {user_agent}")
        body_lines.append("")
        body_lines.append("Message:")
        body_lines.append(message)

        message_obj = EmailMessage()
        message_obj["Subject"] = subject
        message_obj["From"] = self._from_email
        message_obj["To"] = self._to_email
        message_obj["Reply-To"] = email
        message_obj.set_content("\n".join(body_lines))

        try:
            if self._use_ssl:
                with smtplib.SMTP_SSL(
                    self._host, self._port, timeout=10
                ) as smtp:
                    self._login_if_needed(smtp)
                    smtp.send_message(message_obj)
            else:
                with smtplib.SMTP(self._host, self._port, timeout=10) as smtp:
                    if self._use_tls:
                        smtp.starttls()
                    self._login_if_needed(smtp)
                    smtp.send_message(message_obj)
        except BadRequestException:
            raise
        except Exception as exc:
            logger.error("Failed to send contact email: %s", exc)
            raise InfrastructureException("Failed to send contact email.") from exc

    def _login_if_needed(self, smtp: smtplib.SMTP) -> None:
        if self._username and self._password:
            smtp.login(self._username, self._password)
