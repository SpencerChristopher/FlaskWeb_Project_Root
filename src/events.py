"""
This module defines Blinker signals and safe dispatch helpers.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any

from blinker import NamedSignal

logger = logging.getLogger(__name__)

# Define signals
post_created = NamedSignal('post-created')
post_updated = NamedSignal('post-updated')
post_deleted = NamedSignal('post-deleted')
post_published = NamedSignal('post-published')
user_created = NamedSignal('user-created')
user_logged_in = NamedSignal('user-logged-in')
user_deleted = NamedSignal('user-deleted')
user_role_changed = NamedSignal('user-role-changed')


def dispatch_event(signal: NamedSignal, sender: Any, **payload: Any) -> dict[str, Any]:
    """
    Dispatch a signal in best-effort mode.

    Listener exceptions are logged but do not break the caller flow.
    """
    event_payload = dict(payload)
    event_payload.setdefault("event_id", str(uuid.uuid4()))
    event_payload.setdefault(
        "occurred_at",
        datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    event_payload.setdefault("event_type", signal.name)

    for receiver in signal.receivers_for(sender):
        try:
            receiver(sender, **event_payload)
        except Exception:
            logger.exception("Event listener failed for signal=%s", signal.name)

    return event_payload
