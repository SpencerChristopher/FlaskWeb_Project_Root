"""
This module defines the Post model, its schema, and database interactions.
"""

from datetime import datetime
from bson.objectid import ObjectId
from pymongo.database import Database
from typing import List, Dict, Any, Optional

class Post:
    """
    Represents a blog post in the application.

    Attributes:
        title (str): The title of the post.
        slug (str): The URL-friendly slug for the post.
        content (str): The HTML content of the post.
        summary (str): A short summary of the post.
        author_id (ObjectId): The ID of the user who authored the post.
        publication_date (Optional[datetime]): The date the post was published.
        last_updated (datetime): The date the post was last updated.
        is_published (bool): The publication status of the post.
        _id (Optional[ObjectId]): The unique identifier from MongoDB.
    """
    def __init__(self, title: str, slug: str, content: str, summary: str, author_id: ObjectId, 
                 publication_date: Optional[datetime] = None, last_updated: Optional[datetime] = None, 
                 is_published: bool = True, _id: Optional[ObjectId] = None):
        self.title = title
        self.slug = slug
        self.content = content
        self.summary = summary
        self.author_id = author_id
        self.publication_date = publication_date or datetime.utcnow()
        self.last_updated = last_updated or datetime.utcnow()
        self.is_published = is_published
        self._id = _id

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the Post object to a dictionary for JSON responses.

        Returns:
            Dict[str, Any]: A dictionary representation of the post.
        """
        return {
            "_id": str(self._id),  # Convert ObjectId to string
            "title": self.title,
            "slug": self.slug,
            "content": self.content,
            "summary": self.summary,
            "author_id": str(self.author_id),
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "last_updated": self.last_updated.isoformat(),
            "is_published": self.is_published
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Post':
        """
        Creates a Post object from a dictionary.

        Args:
            data (Dict[str, Any]): A dictionary containing post data.

        Returns:
            Post: An instance of the Post class.
        """
        return Post(
            title=data['title'],
            slug=data['slug'],
            content=data['content'],
            summary=data.get('summary', ''),
            author_id=data['author_id'],
            publication_date=data.get('publication_date'),
            last_updated=data.get('last_updated'),
            is_published=data.get('is_published', True),
            _id=data.get('_id')
        )

    @staticmethod
    def create_post(db: Database, title: str, slug: str, content: str, summary: str, author_id: str, is_published: bool) -> Optional[ObjectId]:
        """
        Creates a new post in the database.

        Args:
            db (Database): The database instance.
            title (str): The title of the post.
            slug (str): The URL-friendly slug.
            content (str): The post content.
            summary (str): A short summary of the post.
            author_id (str): The ID of the author.
            is_published (bool): The publication status.

        Returns:
            Optional[ObjectId]: The ObjectId of the newly created post, or None if a post with the same slug already exists.
        """
        if db.posts.find_one({"slug": slug}):
            return None  # Duplicate slug

        post_data = {
            "title": title,
            "slug": slug,
            "content": content,
            "summary": summary,
            "author_id": ObjectId(author_id),
            "publication_date": datetime.utcnow() if is_published else None,
            "last_updated": datetime.utcnow(),
            "is_published": is_published
        }
        result = db.posts.insert_one(post_data)
        return result.inserted_id

    @staticmethod
    def get_all_posts(db: Database, published_only: bool = True) -> List['Post']:
        """
        Retrieves all posts from the database.

        Args:
            db (Database): The database instance.
            published_only (bool): If True, returns only published posts.

        Returns:
            List[Post]: A list of Post objects.
        """
        query = {"is_published": True} if published_only else {}
        posts_data = db.posts.find(query).sort("publication_date", -1)
        return [Post.from_dict(post) for post in posts_data]

    @staticmethod
    def get_post_by_slug(db: Database, slug: str) -> Optional['Post']:
        """
        Retrieves a single post by its slug.

        Args:
            db (Database): The database instance.
            slug (str): The slug of the post.

        Returns:
            Optional[Post]: A Post object if found, otherwise None.
        """
        post_data = db.posts.find_one({"slug": slug})
        return Post.from_dict(post_data) if post_data else None

    @staticmethod
    def get_post_by_id(db: Database, post_id: str) -> Optional['Post']:
        """
        Retrieves a single post by its ObjectId.

        Args:
            db (Database): The database instance.
            post_id (str): The unique identifier of the post.

        Returns:
            Optional[Post]: A Post object if found, otherwise None.
        """
        try:
            post_data = db.posts.find_one({"_id": ObjectId(post_id)})
            return Post.from_dict(post_data) if post_data else None
        except Exception:
            return None

    @staticmethod
    def update_post(db: Database, post_id: str, title: str, slug: str, content: str, summary: str, is_published: bool) -> int:
        """
        Updates an existing post.

        Args:
            db (Database): The database instance.
            post_id (str): The ID of the post to update.
            title (str): The new title.
            slug (str): The new slug.
            content (str): The new content.
            summary (str): The new summary.
            is_published (bool): The new publication status.

        Returns:
            int: The number of documents modified (0 or 1).
        """
        update_data = {
            "$set": {
                "title": title,
                "slug": slug,
                "content": content,
                "summary": summary,
                "last_updated": datetime.utcnow(),
                "is_published": is_published
            }
        }
        if is_published:
            update_data["$set"]["publication_date"] = datetime.utcnow()

        result = db.posts.update_one({"_id": ObjectId(post_id)}, update_data)
        return result.modified_count

    @staticmethod
    def delete_post(db: Database, post_id: str) -> int:
        """
        Deletes a post from the database.

        Args:
            db (Database): The database instance.
            post_id (str): The ID of the post to delete.

        Returns:
            int: The number of documents deleted (0 or 1).
        """
        result = db.posts.delete_one({"_id": ObjectId(post_id)})
        return result.deleted_count

