"""
This module defines the Comment model using MongoEngine.
"""
import datetime
from src.extensions import db
from src.models.article import Article
from src.models.user import User
from mongoengine.fields import ReferenceField

class Comment(db.Document):
    """
    Represents a user comment on a blog article.
    """
    content = db.StringField(required=True, max_length=1000)
    author = ReferenceField('User')
    article = ReferenceField('Article')
    created_at = db.DateTimeField(default=datetime.datetime.utcnow)
    is_approved = db.BooleanField(default=True)

    def to_dict(self) -> dict:
        """Serializes the Comment to a dictionary."""
        return {
            "id": str(self.id),
            "content": self.content,
            "author": {
                "id": str(self.author.id),
                "username": self.author.username
            },
            "article_id": str(self.article.id),
            "created_at": self.created_at.isoformat(),
        }

    meta = {
        'collection': 'comments',
        'indexes': ['article', '-created_at']
    }
