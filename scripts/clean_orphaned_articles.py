import os
import sys

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.models.article import Article
from mongoengine.errors import DoesNotExist
from scripts.utils import get_flask_app_context

def clean_orphaned_articles():
    """
    Deletes articles where the author reference is broken or missing.
    """
    # Set up Flask app context
    app_context = get_flask_app_context()
    
    print("Searching for orphaned articles...")
    orphaned_articles = []
    try:
        for article in Article.objects():
            try:
                # Accessing the author triggers the check.
                # A DoesNotExist error occurs if the referenced author is gone.
                _ = article.author.id
            except DoesNotExist:
                orphaned_articles.append(article)

        if orphaned_articles:
            print(f"Found {len(orphaned_articles)} orphaned articles. Deleting...")
            for article in orphaned_articles:
                print(f"Deleting article titled '{article.title}' (ID: {article.id})")
                article.delete()
            print("Orphaned articles deleted successfully.")
        else:
            print("No orphaned articles found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the context is popped
        app_context.pop()

if __name__ == '__main__':
    clean_orphaned_articles()
