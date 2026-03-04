"""
This module defines and registers event listeners for the application.
"""
import logging
from flask import current_app
from src.events import article_created, article_updated, article_deleted, user_logged_in, user_deleted

logger = logging.getLogger(__name__)

def cleanup_comments_on_article_delete(sender, **kwargs):
    """
    Listener that deletes all comments associated with a deleted article.
    """
    article_id = kwargs.get("article_id")
    if not article_id:
        return

    from src.repositories import get_comment_repository
    comment_repo = get_comment_repository()
    try:
        delete_result = comment_repo.delete_by_article_id(article_id)
        current_app.logger.info(
            f"Cleanup: Deleted {delete_result} comments for article_id={article_id}"
        )
    except Exception as e:
        logger.error(
            "Cleanup failed for article_id %s: %s",
            article_id,
            e,
            exc_info=True,
        )

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
article_created.connect(log_blinker_event)
article_updated.connect(log_blinker_event)
article_deleted.connect(log_blinker_event)
article_deleted.connect(cleanup_comments_on_article_delete)
user_logged_in.connect(log_blinker_event)
user_deleted.connect(log_blinker_event)
