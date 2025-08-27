"""
This module defines Blinker signals for the application's event system.
"""
from blinker import NamedSignal

# Define signals
post_created = NamedSignal('post-created')
post_updated = NamedSignal('post-updated')
post_deleted = NamedSignal('post-deleted')
user_logged_in = NamedSignal('user-logged-in')