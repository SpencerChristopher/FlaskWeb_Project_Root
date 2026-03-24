"""
Turnstile verification service for bot protection.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class TurnstileService:
    """Verify Cloudflare Turnstile tokens server-side.

    Args:
        secret_key: Turnstile secret key.
        enabled: Whether verification is enforced.
        verify_url: Turnstile verification endpoint.
        timeout_seconds: Network timeout for verification calls.
    """

    def __init__(
        self,
        secret_key: str | None,
        *,
        enabled: bool = True,
        verify_url: str = "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        timeout_seconds: int = 5,
    ) -> None:
        self._secret_key = secret_key
        self._enabled = enabled
        self._verify_url = verify_url
        self._timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        """Return whether Turnstile verification is enforced."""
        return self._enabled

    def verify_token(self, token: str | None, remote_ip: str | None = None) -> bool:
        """Verify a Turnstile token.

        Returns:
            bool: True if the token is valid or Turnstile is disabled.
        """
        if not self._enabled:
            return True
        if not token or not self._secret_key:
            return False

        payload: dict[str, Any] = {"secret": self._secret_key, "response": token}
        if remote_ip:
            payload["remoteip"] = remote_ip

        try:
            response = requests.post(
                self._verify_url, data=payload, timeout=self._timeout_seconds
            )
            data = response.json()
            return bool(data.get("success"))
        except Exception as err:
            logger.warning("Turnstile verification failed: %s", err)
            return False
