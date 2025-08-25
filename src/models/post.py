"""
This module defines the Post model using MongoEngine.
"""
from src.extensions import db
from src.models.user import User
import datetime
from mongoengine.fields import ReferenceField
from src.events import event_dispatcher, PostCreatedEvent, PostUpdatedEvent, PostDeletedEvent

class Post(db.Document):
    """
    Represents a blog post in the application.
    """
    title = db.StringField(required=True, max_length=200)
    slug = db.StringField(required=True, unique=True)
    content = db.StringField(required=True)
    summary = db.StringField(max_length=400)
    author = ReferenceField(User, required=True)
    publication_date = db.DateTimeField()
    last_updated = db.DateTimeField(default=datetime.datetime.utcnow)
    is_published = db.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        Saves the Post document to the database.

        Automatically sets publication_date if it's a new published post
        and updates last_updated. Dispatches PostCreatedEvent or PostUpdatedEvent.

        Returns:
            Post: The saved Post instance.
        """
        is_new = self.id is None # Check if it's a new document
        
        if not self.publication_date and self.is_published:
            self.publication_date = datetime.datetime.utcnow()
        self.last_updated = datetime.datetime.utcnow()
        
        super(Post, self).save(*args, **kwargs) # Call super save first to get an ID if new

        if is_new:
            event_dispatcher.dispatch(PostCreatedEvent(post_id=str(self.id), user_id=str(self.author.id)))
        else:
            # For updates, you might want to pass specific changes,
            # but for simplicity, we'll just pass the ID for now.
            event_dispatcher.dispatch(PostUpdatedEvent(post_id=str(self.id), user_id=str(self.author.id), changes={}))
        
        return self

    def delete(self, *args, **kwargs):
        """
        Deletes the Post document from the database.

        Dispatches a PostDeletedEvent after successful deletion.
        """
        post_id = str(self.id)
        user_id = str(self.author.id) # Capture before deletion
        super(Post, self).delete(*args, **kwargs)
        event_dispatcher.dispatch(PostDeletedEvent(post_id=post_id, user_id=user_id))

    def to_dict(self) -> dict:
        """
        Serializes the Post object to a dictionary for JSON responses.
        """
        return {
            "id": str(self.id),
            "title": self.title,
            "slug": self.slug,
            "content": self.content,
            "summary": self.summary,
            "author": str(self.author.id),
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "last_updated": self.last_updated.isoformat(),
            "is_published": self.is_published
        }

    meta = {
        'collection': 'posts',
        'indexes': ['slug', '-publication_date']
    }