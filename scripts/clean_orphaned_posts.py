
import os
import sys
from dotenv import load_dotenv

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.models.post import Post
from src.models.user import User
from src.extensions import db
from flask import Flask
from mongoengine.errors import DoesNotExist

# Load environment variables
load_dotenv()

# Create a minimal Flask app context for MongoEngine
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'host': os.environ.get('MONGO_URI')
}
db.init_app(app)

# Push an application context
app_context = app.app_context()
app_context.push()


def clean_orphaned_posts():
    """
    Deletes posts with no author.
    """
    orphaned_posts = []
    for post in Post.objects():
        try:
            # This will trigger a DoesNotExist error if the author is missing
            _ = post.author.id
        except DoesNotExist:
            orphaned_posts.append(post)

    if orphaned_posts:
        print(f"Found {len(orphaned_posts)} orphaned posts. Deleting...")
        for post in orphaned_posts:
            print(f"Deleting post with ID: {post.id}")
            post.delete()
        print("Orphaned posts deleted successfully.")
    else:
        print("No orphaned posts found.")

if __name__ == '__main__':
    clean_orphaned_posts()

# Pop the application context
app_context.pop()
