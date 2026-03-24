"""
Guards for contact form submissions (honeypot + timing).
"""

from __future__ import annotations

import time
from typing import Callable, Iterable

from src.exceptions import BadRequestException


class ContactGuard:
    """Lightweight bot defenses for contact submissions.

    Args:
        min_time_ms: Minimum milliseconds between form load and submit.
        honeypot_fields: Field names that must remain empty.
        time_provider: Callable returning current time in seconds.
    """

    def __init__(
        self,
        *,
        min_time_ms: int = 1500,
        honeypot_fields: Iterable[str] | None = None,
        time_provider: Callable[[], float] | None = None,
    ) -> None:
        self._min_time_ms = min_time_ms
        self._honeypot_fields = tuple(honeypot_fields or ("website", "company"))
        self._time_provider = time_provider or time.time

    def validate(self, payload: dict) -> None:
        """Validate honeypot and timing checks.

        Raises:
            BadRequestException: If bot signals are detected.
        """
        for field in self._honeypot_fields:
            if payload.get(field):
                raise BadRequestException("Bot detection triggered.")

        loaded_at = payload.get("form_loaded_at")
        if loaded_at is None:
            return

        try:
            loaded_at_ms = int(loaded_at)
        except (TypeError, ValueError) as exc:
            raise BadRequestException("Invalid form timestamp.") from exc

        now_ms = int(self._time_provider() * 1000)
        if now_ms - loaded_at_ms < self._min_time_ms:
            raise BadRequestException("Form submitted too quickly.")
