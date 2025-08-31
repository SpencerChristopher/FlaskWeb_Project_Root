import os
import sys

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.models.post import Post
from mongoengine.errors import DoesNotExist
from scripts.utils import get_flask_app_context

def clean_orphaned_posts():
    """
    Deletes posts where the author reference is broken or missing.
    """
    # Set up Flask app context
    app_context = get_flask_app_context()
    
    print("Searching for orphaned posts...")
    orphaned_posts = []
    try:
        for post in Post.objects():
            try:
                # Accessing the author triggers the check.
                # A DoesNotExist error occurs if the referenced author is gone.
                _ = post.author.id
            except DoesNotExist:
                orphaned_posts.append(post)

        if orphaned_posts:
            print(f"Found {len(orphaned_posts)} orphaned posts. Deleting...")
            for post in orphaned_posts:
                print(f"Deleting post titled '{post.title}' (ID: {post.id})")
                post.delete()
            print("Orphaned posts deleted successfully.")
        else:
            print("No orphaned posts found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the context is popped
        app_context.pop()

if __name__ == '__main__':
    clean_orphaned_posts()