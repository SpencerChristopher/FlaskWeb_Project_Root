"""
Central signal definitions for the application event system.
Uses Blinker for decoupled cross-module communication.
"""

from __future__ import annotations
import datetime
import logging
import uuid
from typing import Any
from blinker import NamedSignal

logger = logging.getLogger(__name__)

# --- User Events ---
user_logged_in = NamedSignal('user-logged-in')
user_logged_out = NamedSignal('user-logged-out')
user_created = NamedSignal('user-created')
user_deleted = NamedSignal('user-deleted')
user_role_changed = NamedSignal('user-role-changed')

# --- Article Events ---
article_created = NamedSignal('article-created')
article_updated = NamedSignal('article-updated')
article_deleted = NamedSignal('article-deleted')
article_published = NamedSignal('article-published')

# Legacy Aliases
post_created = article_created
post_updated = article_updated
post_deleted = article_deleted
post_published = article_published

# --- Profile Events ---
profile_updated = NamedSignal('profile-updated')

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
