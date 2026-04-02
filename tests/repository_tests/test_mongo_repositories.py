import datetime

from src.models.post import Post
from src.models.user import User
from src.repositories.mongo_post_repository import MongoPostRepository
from src.repositories.mongo_user_repository import MongoUserRepository


def test_user_repository_lookup_by_username_and_id(app):
    user_repository = MongoUserRepository()

    with app.app_context():
        user = User(username="repo_user", email="repo_user@example.com", role="member")
        user.set_password("Password123!")
        user.save()

        by_username = user_repository.get_by_username("repo_user")
        assert by_username is not None
        assert by_username.email == "repo_user@example.com"

        by_id = user_repository.get_by_id(str(user.id))
        assert by_id is not None
        assert by_id.username == "repo_user"

        user_repository.delete(user)
        assert user_repository.get_by_id(str(user.id)) is None


def test_post_repository_published_pagination_and_slug_helpers(app):
    post_repository = MongoPostRepository()

    with app.app_context():
        author = User(username="repo_author", email="repo_author@example.com", role="admin")
        author.set_password("Password123!")
        author.save()

        published_post = Post(
            title="Repository Published Post",
            slug="repository-published-post",
            content="Published content",
            summary="Published summary",
            author=author,
            is_published=True,
            publication_date=datetime.datetime.now(datetime.UTC),
        )
        post_repository.save(published_post)

        draft_post = Post(
            title="Repository Draft Post",
            slug="repository-draft-post",
            content="Draft content",
            summary="Draft summary",
            author=author,
            is_published=False,
        )
        post_repository.save(draft_post)

        paginated = post_repository.get_published_paginated(page=1, per_page=10)
        assert paginated.total == 1
        assert len(paginated.items) == 1
        assert paginated.items[0].slug == "repository-published-post"

        found_post = post_repository.get_by_slug("repository-published-post")
        assert found_post is not None
        assert str(found_post.id) == str(published_post.id)

        excluded = post_repository.get_by_slug_excluding_id(
            slug="repository-published-post",
            post_id=str(published_post.id),
        )
        assert excluded is None
