"""
This module defines the Post model using MongoEngine.
"""
from src.extensions import db
from src.models.user import User
import datetime
from mongoengine.fields import ReferenceField
from mongoengine.errors import DoesNotExist


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
