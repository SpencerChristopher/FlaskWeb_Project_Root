"""
This module defines and registers event listeners for the application.

Listeners subscribe to specific events dispatched by the EventDispatcher
and perform actions in response.
"""
from flask import current_app
from src.events import post_created, post_updated, post_deleted, user_logged_in, user_deleted
from src.models.token_blocklist import TokenBlocklist
from flask_jwt_extended import get_jwt, verify_jwt_in_request
import datetime

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

def blacklist_user_tokens(sender, user_id):
    """
    Listener to blacklist JWT tokens when a user is deleted.
    """
    try:
        with current_app.app_context():
            # Check if there's a JWT in the current request context
            if verify_jwt_in_request(optional=True):
                jti = get_jwt()["jti"]
                expires = datetime.datetime.fromtimestamp(get_jwt()["exp"])

                # Add the token to the blocklist
                blocklisted_token = TokenBlocklist(jti=jti, expires_at=expires)
                blocklisted_token.save()
                current_app.logger.info(f"Token {jti} for user {user_id} blacklisted.")
            else:
                current_app.logger.warning(f"No JWT in request context for user {user_id} deletion. Cannot blacklist current token.")
    except Exception as e:
        current_app.logger.error(
            f"Error blacklisting token for user {user_id}: {e}",
            exc_info=True
        )


# Register listeners
post_created.connect(log_blinker_event)
post_updated.connect(log_blinker_event)
post_deleted.connect(log_blinker_event)
user_logged_in.connect(log_blinker_event)
user_deleted.connect(log_blinker_event) # Log user_deleted event
user_deleted.connect(blacklist_user_tokens) # Blacklist tokens on user_deleted
