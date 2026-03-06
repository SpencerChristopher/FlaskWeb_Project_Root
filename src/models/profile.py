"""
This module defines the Profile model for the developer profile.
Uses pure mongoengine fields to avoid WTForms mixin conflicts.
"""
import mongoengine
import datetime
from src.extensions import db

PROFILE_SINGLETON_KEY = "profile"

class WorkHistoryItem(mongoengine.EmbeddedDocument):
    """Represents a single employment entry."""
    company = mongoengine.StringField(required=True)
    role = mongoengine.StringField(required=True)
    start_date = mongoengine.StringField(required=True)
    end_date = mongoengine.StringField(default="Present")
    location = mongoengine.StringField(required=True)
    description = mongoengine.StringField()
    skills = mongoengine.ListField(mongoengine.StringField())

class Profile(db.Document):
    """
    Represents the site owner's developer profile.
    This is intended to be a singleton-style document.
    """
    name = mongoengine.StringField(required=True, max_length=100)
    headline_role = mongoengine.StringField(max_length=100) # Optional headline override
    location = mongoengine.StringField(required=True, max_length=100)
    statement = mongoengine.StringField(required=True, max_length=2000)
    interests = mongoengine.ListField(mongoengine.StringField(max_length=50))
    skills = mongoengine.ListField(mongoengine.StringField(max_length=50))
    singleton_key = mongoengine.StringField(required=True, unique=True, default=PROFILE_SINGLETON_KEY)
    social_links = mongoengine.DictField()
    work_history = mongoengine.EmbeddedDocumentListField(WorkHistoryItem)
    image_url = mongoengine.StringField()
    last_updated = mongoengine.DateTimeField(default=datetime.datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "headline_role": self.headline_role,
            "location": self.location,
            "statement": self.statement,
            "interests": self.interests,
            "skills": self.skills,
            "social_links": self.social_links or {},
            "work_history": [item.to_mongo().to_dict() for item in self.work_history],
            "image_url": self.image_url,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

    meta = {
        'collection': 'profiles'
    }
