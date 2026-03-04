import pytest
from src.events import article_created
from src.exceptions import ConflictException, ForbiddenException, UnauthorizedException
from src.models.user import User
from src.services import get_authz_service, get_article_service
from src.schemas import ArticleCreateUpdate, UserIdentity

def test_article_service_create_conflict(app):
    article_service = get_article_service()
    with app.app_context():
        author = User(username="svc_admin", email="svc@test.com", role="admin")
        author.set_password("Password123!")
        author.save()
        user_identity = UserIdentity(id=str(author.id), username=author.username, role=author.role, token_version=0)
        dto = ArticleCreateUpdate(title="Svc Art", content="C", summary="S", is_published=True)
        article_service.create_article(article_dto=dto, user=user_identity)
        with pytest.raises(ConflictException):
            article_service.create_article(article_dto=dto, user=user_identity)
        author.delete()

def test_article_service_list_published(app):
    article_service = get_article_service()
    with app.app_context():
        author = User(username="svc_writer", email="writer@test.com", role="admin")
        author.set_password("Password123!")
        author.save()
        user_identity = UserIdentity(id=str(author.id), username=author.username, role=author.role, token_version=0)
        article_service.create_article(
            article_dto=ArticleCreateUpdate(title="P", content="C", summary="S", is_published=True),
            user=user_identity
        )
        article_service.create_article(
            article_dto=ArticleCreateUpdate(title="D", content="C", summary="S", is_published=False),
            user=user_identity
        )
        paginated = article_service.list_published_articles(page=1, per_page=10)
        assert paginated.total == 1
        author.delete()
