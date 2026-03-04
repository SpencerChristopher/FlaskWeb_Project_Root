import datetime

from mongoengine import get_db

from src.models.profile import Profile, PROFILE_SINGLETON_KEY
from src.repositories import get_profile_repository


def _profile_payload():
    return {
        "name": "Dev Name",
        "location": "Remote",
        "statement": "Welcome to my developer profile.",
        "interests": [],
        "skills": [],
        "social_links": {},
        "work_history": [],
        "image_url": None,
        "last_updated": datetime.datetime.utcnow(),
    }


def test_profile_singleton_key_assigned_on_raw_doc(app):
    with app.app_context():
        db = get_db()
        collection = db.get_collection(Profile._get_collection_name())
        collection.insert_one(_profile_payload())

        repo = get_profile_repository()
        profile = repo.get_profile()

        assert profile is not None
        assert profile.singleton_key == PROFILE_SINGLETON_KEY


def test_profile_save_enforces_singleton_key(app):
    with app.app_context():
        repo = get_profile_repository()
        profile = Profile(**_profile_payload(), singleton_key="other")

        saved = repo.save(profile)

        assert saved.singleton_key == PROFILE_SINGLETON_KEY
