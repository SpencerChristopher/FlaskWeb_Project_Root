from datetime import datetime
from bson.objectid import ObjectId

class Post:
    def __init__(self, title, slug, content, summary, author_id, publication_date=None, last_updated=None, is_published=True, _id=None):
        self.title = title
        self.slug = slug
        self.content = content
        self.summary = summary
        self.author_id = author_id # ObjectId of the author
        self.publication_date = publication_date if publication_date else datetime.utcnow()
        self.last_updated = last_updated if last_updated else datetime.utcnow()
        self.is_published = is_published
        self._id = _id # MongoDB ObjectId

    def to_dict(self):
        return {
            "title": self.title,
            "slug": self.slug,
            "content": self.content,
            "summary": self.summary,
            "author_id": self.author_id,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "is_published": self.is_published
        }

    @staticmethod
    def from_dict(data):
        return Post(
            title=data['title'],
            slug=data['slug'],
            content=data['content'],
            summary=data['summary'],
            author_id=data['author_id'],
            publication_date=data.get('publication_date') or data.get('published_date'), # Handle both
            last_updated=data.get('last_updated') or data.get('created_at'), # Handle both
            is_published=data.get('is_published', True),
            _id=data.get('_id')
        )

    def create_post(db, title, content, summary, slug, is_published, author_id):
        if Post.find_by_slug(db, slug):
            return None # Post with this slug already exists

        new_post = Post(
            title=title,
            content=content,
            summary=summary,
            slug=slug,
            is_published=is_published,
            published_date=datetime.utcnow() if is_published else None,
            created_at=datetime.utcnow(),
            author_id=author_id
        )
        
        result = db.posts.insert_one({
            "title": new_post.title,
            "content": new_post.content,
            "summary": new_post.summary,
            "slug": new_post.slug,
            "is_published": new_post.is_published,
            "published_date": new_post.published_date,
            "created_at": new_post.created_at,
            "author_id": new_post.author_id
        })
        new_post._id = result.inserted_id
        return new_post

    def to_dict(self):
        return {
            "_id": str(self._id), # Convert ObjectId to string for JSON serialization
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "slug": self.slug,
            "is_published": self.is_published,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "author_id": self.author_id
        }

    @staticmethod
    def get_all_posts(db, published_only=True):
        query = {"is_published": True} if published_only else {}
        posts_data = db.posts.find(query).sort("publication_date", -1)
        return [Post.from_dict(post) for post in posts_data]

    @staticmethod
    def get_post_by_slug(db, slug):
        post_data = db.posts.find_one({"slug": slug})
        if post_data:
            return Post.from_dict(post_data)
        return None

    @staticmethod
    def get_post_by_id(db, post_id):
        post_data = db.posts.find_one({"_id": ObjectId(post_id)})
        if post_data:
            return Post.from_dict(post_data)
        return None

    @staticmethod
    def update_post(db, post_id, title, slug, content, is_published):
        result = db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {
                "title": title,
                "slug": slug,
                "content": content,
                "last_updated": datetime.utcnow(),
                "is_published": is_published
            }}
        )
        return result.modified_count > 0

    @staticmethod
    def delete_post(db, post_id):
        result = db.posts.delete_one({"_id": ObjectId(post_id)})
        return result.deleted_count > 0
