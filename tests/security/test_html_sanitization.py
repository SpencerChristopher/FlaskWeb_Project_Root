import pytest
from src.models.article import Article
from src.models.user import User
from src.services import get_article_service
from src.schemas import ArticleCreateUpdate, UserIdentity


@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(username="testuser", email="test@test.com", role="admin")
        user.set_password("password")
        user.save()
        yield user
        user.delete()


class TestHtmlSanitization:
    def test_malicious_script_tag_removed(self, app, test_user):
        article_service = get_article_service()
        with app.app_context():
            user_identity = UserIdentity(
                id=str(test_user.id),
                username=test_user.username,
                role=test_user.role,
                token_version=0,
            )
            dto = ArticleCreateUpdate(
                title="XSS",
                content="<script>alert(1)</script>Safe",
                summary="S",
                is_published=True,
            )
            art = article_service.create_article(article_dto=dto, user=user_identity)
            assert "<script>" not in art.content
