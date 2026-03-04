"""
This module defines the Article model for blog content.
"""
import mongoengine
import datetime
from src.extensions import db
from src.models.user import User

class Article(db.Document):
    """
    Represents a blog article. 
    Pinned to 'posts' collection for legacy compatibility during refactor.
    Uses string reference for User to break circular imports.
    """
    title = mongoengine.StringField(required=True, max_length=200)
    slug = mongoengine.StringField(required=True, unique=True)
    content = mongoengine.StringField(required=True)
    summary = mongoengine.StringField(max_length=500)
    author = mongoengine.ReferenceField('User', reverse_delete_rule=mongoengine.CASCADE, required=True)
    is_published = mongoengine.BooleanField(default=False)
    publication_date = mongoengine.DateTimeField()
    last_updated = mongoengine.DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        'collection': 'posts',
        'indexes': [
            'slug',
            '-publication_date'
        ]
    }

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "title": self.title,
            "slug": self.slug,
            "content": self.content,
            "summary": self.summary,
            "is_published": self.is_published,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "author_id": str(self.author.id) if self.author else None,
            "author_username": self.author.username if self.author else None
        }
