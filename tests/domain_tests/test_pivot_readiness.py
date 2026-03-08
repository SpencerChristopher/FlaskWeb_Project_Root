import pytest
from src.models.user import User
from src.models.article import Article
from src.events import article_deleted
from src.models.comment import Comment


class TestPivotReadiness:
    def test_gate_referential_integrity_on_delete(self, app, signal_tracker):
        from src.services import get_article_service

        article_service = get_article_service()

        with app.app_context():
            author = User(username="pivot_author", email="pivot@test.com", role="admin")
            author.set_password("password")
            author.save()

            from src.schemas import ArticleCreateUpdate, UserIdentity

            dto = ArticleCreateUpdate(
                title="Integrity Test", content="C", summary="S", is_published=True
            )
            user_identity = UserIdentity(
                id=str(author.id),
                username=author.username,
                role=author.role,
                token_version=0,
            )

            art = article_service.create_article(article_dto=dto, user=user_identity)
            article_id = str(art.id)

            for i in range(3):
                Comment(content=f"Comment {i}", author=author, article=art).save()

            assert Comment.objects(article=article_id).count() == 3

            with signal_tracker(article_deleted) as tracker:
                article_service.delete_article(article_id, user=user_identity)
                assert tracker.called
                assert tracker.data["article_id"] == article_id

            assert Comment.objects(article=article_id).count() == 0
            author.delete()
