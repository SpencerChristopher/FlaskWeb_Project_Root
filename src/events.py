"""
This module defines the event classes and the EventDispatcher for the application's
Observer design pattern implementation.
"""
from typing import Callable, Dict, List, Any

class Event:
    """Base class for all application events."""
    pass

class PostCreatedEvent(Event):
    def __init__(self, post_id: str, user_id: str):
        """
        Initializes a PostCreatedEvent.

        Args:
            post_id (str): The ID of the newly created post.
            user_id (str): The ID of the user who created the post.
        """
        self.post_id = post_id
        self.user_id = user_id

class PostUpdatedEvent(Event):
    def __init__(self, post_id: str, user_id: str, changes: Dict[str, Any]):
        """
        Initializes a PostUpdatedEvent.

        Args:
            post_id (str): The ID of the updated post.
            user_id (str): The ID of the user who updated the post.
            changes (Dict[str, Any]): A dictionary of changes made to the post.
        """
        self.post_id = post_id
        self.user_id = user_id
        self.changes = changes

class PostDeletedEvent(Event):
    def __init__(self, post_id: str, user_id: str):
        """
        Initializes a PostDeletedEvent.

        Args:
            post_id (str): The ID of the deleted post.
            user_id (str): The ID of the user who deleted the post.
        """
        self.post_id = post_id
        self.user_id = user_id

class UserLoggedInEvent(Event):
    def __init__(self, user_id: str):
        """
        Initializes a UserLoggedInEvent.

        Args:
            user_id (str): The ID of the user who logged in.
        """
        self.user_id = user_id

class EventDispatcher:
    """A simple in-memory event dispatcher."""
    def __init__(self):
        """Initializes the EventDispatcher."""
        self._listeners: Dict[type, List[Callable[[Event], None]]] = {}

    def listen(self, event_type: type, listener: Callable[[Event], None]):
        """Register a listener for a specific event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def dispatch(self, event: Event):
        """Dispatch an event to all registered listeners."""
        event_type = type(event)
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                try:
                    listener(event)
                except Exception as e:
                    # Log the error, but don't stop other listeners
                    print(f"Error dispatching event {event_type.__name__} to listener {listener.__name__}: {e}")

# Global event dispatcher instance
# This can be imported and used throughout the application
event_dispatcher = EventDispatcher()
