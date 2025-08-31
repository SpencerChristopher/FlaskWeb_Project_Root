"""
This module defines the Post model using MongoEngine.
"""
from src.extensions import db
from src.models.user import User
import datetime
from datetime import timezone
from mongoengine.fields import ReferenceField
from mongoengine.errors import DoesNotExist
from src.events import post_created, post_updated, post_deleted
import bleach


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
    last_updated = db.DateTimeField(default=datetime.datetime.now(datetime.timezone.utc))
    is_published = db.BooleanField(default=False)


    def save(self, *args, **kwargs):
        """
        Saves the Post document to the database.

        Automatically sets publication_date if it's a new published post
        and updates last_updated. Dispatches PostCreatedEvent or PostUpdatedEvent.

        Returns:
            Post: The saved Post instance.
        """
        is_new = self.id is None  # Check if it's a new document

        if not self.publication_date and self.is_published:
            self.publication_date = datetime.datetime.now(datetime.timezone.utc)
        self.last_updated = datetime.datetime.now(datetime.timezone.utc)

        # Sanitize content and summary before saving
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'p', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        allowed_attributes = {'a': ['href', 'title'], 'abbr': ['title'], 'acronym': ['title']}

        self.content = bleach.clean(self.content, tags=allowed_tags, attributes=allowed_attributes, strip=True)
        self.summary = bleach.clean(self.summary, tags=allowed_tags, attributes=allowed_attributes, strip=True)

        super(Post, self).save(*args, **kwargs)  # Call super save first to get an ID if new

        if is_new:
            post_created.send(self, post_id=str(self.id), user_id=str(self.author.id))
        else:
            # For updates, you might want to pass specific changes,
            # but for simplicity, we'll just pass the ID for now.
            post_updated.send(self, post_id=str(self.id), user_id=str(self.author.id), changes={})
        
        return self


    def delete(self, *args, **kwargs):
        """
        Deletes the Post document from the database.

        Dispatches a PostDeletedEvent after successful deletion.
        """
        post_id = str(self.id)
        user_id = None
        try:
            user_id = str(self.author.id)
        except DoesNotExist:
            pass
        super(Post, self).delete(*args, **kwargs)
        if user_id:
            post_deleted.send(self, post_id=post_id, user_id=user_id)


    def to_dict(self) -> dict:
        """
        Serializes the Post object to a dictionary for JSON responses.
        """
        try:
            author_id = str(self.author.id)
        except DoesNotExist:
            author_id = None

        return {
            "id": str(self.id),
            "title": self.title,
            "slug": self.slug,
            "content": self.content,
            "summary": self.summary,
            "author": {
                "id": str(self.author.id),
                "username": self.author.username
            },
            "publication_date": (
                self.publication_date.isoformat()
                if self.publication_date
                else None
            ),
            "last_updated": self.last_updated.isoformat(),
            "is_published": self.is_published,
        }


    meta = {
        'collection': 'posts',
        'indexes': ['slug', '-publication_date']
    }
