import datetime
import pytest

from src.models.user import User
from src.models.article import Article
from src.repositories.mongo_article_repository import MongoArticleRepository
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


def test_article_repository_published_pagination_and_slug_helpers(app):
    article_repository = MongoArticleRepository()

    with app.app_context():
        author = User(username="repo_author", email="repo_author@example.com", role="admin")
        author.set_password("Password123!")
        author.save()

        published_art = Article(
            title="Repository Published Article",
            slug="repository-published-article",
            content="Published content",
            summary="Published summary",
            author=author,
            is_published=True,
            publication_date=datetime.datetime.now(datetime.timezone.utc),
        )
        article_repository.save(published_art)

        draft_art = Article(
            title="Repository Draft Article",
            slug="repository-draft-article",
            content="Draft content",
            summary="Draft summary",
            author=author,
            is_published=False,
        )
        article_repository.save(draft_art)

        paginated = article_repository.get_published_paginated(page=1, per_page=10)
        assert paginated.total == 1
        assert len(paginated.items) == 1
        assert paginated.items[0].slug == "repository-published-article"

        found_art = article_repository.get_by_slug("repository-published-article")
        assert found_art is not None
        assert str(found_art.id) == str(published_art.id)

        excluded = article_repository.get_by_slug_excluding_id(
            slug="repository-published-article",
            article_id=str(published_art.id),
        )
        assert excluded is None
