"""
This module defines and registers event listeners for the application.

Listeners subscribe to specific events dispatched by the EventDispatcher
and perform actions in response.
"""
import logging

from flask import current_app
from src.events import post_created, post_updated, post_deleted, user_logged_in, user_deleted

logger = logging.getLogger(__name__)

def log_blinker_event(sender, **kwargs):
    """A generic listener that logs all dispatched Blinker events."""
    event_name = kwargs.get("event_type", "unknown_signal")
    event_id = kwargs.get("event_id", "unknown")
    log_message = f"Blinker Event Dispatched: {event_name} event_id={event_id}"
    if kwargs:
        log_message += f" - Data: {kwargs}"

    try:
        current_app.logger.info(log_message)
    except Exception as e:
        logger.error(
            "Error in log_blinker_event for event '%s': %s",
            event_name,
            e,
            exc_info=True,
        )


# Register listeners
post_created.connect(log_blinker_event)
post_updated.connect(log_blinker_event)
post_deleted.connect(log_blinker_event)
user_logged_in.connect(log_blinker_event)
user_deleted.connect(log_blinker_event)
