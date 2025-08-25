"""
This module defines and registers event listeners for the application.

Listeners subscribe to specific events dispatched by the EventDispatcher
and perform actions in response.
"""
from src.events import event_dispatcher, Event, PostCreatedEvent, PostUpdatedEvent, PostDeletedEvent, UserLoggedInEvent
from flask import current_app

def log_event(event: Event):
    """A generic listener that logs all dispatched events."""
    # Ensure we are in an application context
    with current_app.app_context():
        current_app.logger.info(f"Event Dispatched: {event.__class__.__name__} - {event.__dict__}")

# Register listeners
event_dispatcher.listen(Event, log_event) # Listen to all events (base Event class)
