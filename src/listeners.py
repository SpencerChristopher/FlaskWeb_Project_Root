"""
This module defines and registers event listeners for the application.

Listeners subscribe to specific events dispatched by the EventDispatcher
and perform actions in response.
"""
from flask import current_app
from src.events import post_created, post_updated, post_deleted, user_logged_in

def log_blinker_event(sender, **kwargs):
    """A generic listener that logs all dispatched Blinker events."""
    try:
        with current_app.app_context():
            event_name = sender.name if hasattr(sender, 'name') else 'unknown_signal'
            log_message = f"Blinker Event Dispatched: {event_name} from {sender.__class__.__name__}"
            if kwargs:
                log_message += f" - Data: {kwargs}"
            current_app.logger.info(log_message)
    except Exception as e:
        # Log the error within the listener itself
        current_app.logger.error(
            f"Error in log_blinker_event listener for signal {sender.name}: {e}",
            exc_info=True
        )


# Register listeners
post_created.connect(log_blinker_event)
post_updated.connect(log_blinker_event)
post_deleted.connect(log_blinker_event)
user_logged_in.connect(log_blinker_event)
