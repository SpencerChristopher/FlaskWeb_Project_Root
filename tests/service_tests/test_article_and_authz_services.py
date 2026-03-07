import pytest

from src.exceptions import ConflictException, UnauthorizedException
from src.models.user import User
from src.schemas import ArticleCreateUpdate, UserIdentity
from src.services import get_article_service

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


def test_article_service_create_requires_valid_user(app):
    """
    Verify that the system requires a valid user for article creation.
    Note: ArticleService trusts the UserIdentity provided by AuthzService.
    Verification of user existence happens in AuthzService.
    """
    from src.services import get_authz_service
    authz_service = get_authz_service()
    
    with app.app_context():
        user_id = "65f0b4b4b4b4b4b4b4b4b4b4"
        user_claims = {"un": "missing", "roles": ["admin"], "tv": 0}
        
        # AuthzService should raise UnauthorizedException if the user doesn't exist in DB
        with pytest.raises(UnauthorizedException):
            authz_service.require_permission(user_id, user_claims, "content:manage")
