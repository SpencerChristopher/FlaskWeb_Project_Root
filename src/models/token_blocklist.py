from src.extensions import db
import datetime

class TokenBlocklist(db.Document):
    jti = db.StringField(required=True, unique=True)
    created_at = db.DateTimeField(default=datetime.datetime.now)
    expires_at = db.DateTimeField(required=True)

    meta = {
        'collection': 'token_blocklist',
        'indexes': [
            {'fields': ['expires_at'], 'expireAfterSeconds': 0} # TTL index
        ]
    }
