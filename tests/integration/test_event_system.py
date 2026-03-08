import pytest
from src.events import (
    user_role_changed,
    article_published,
    article_created,
    article_updated,
    article_deleted,
)
from src.models.user import User
from src.models.article import Article
from src.services import get_auth_service, get_article_service
from src.schemas import ArticleCreateUpdate, UserIdentity


class TestEventSystem:
    def test_user_role_change_emits_signal(self, app, signal_tracker):
        auth_service = get_auth_service()
        with app.app_context():
            user = User(username="event_user", email="event@test.com", role="member")
            user.set_password("password")
            user.save()
            user_id = str(user.id)
            with signal_tracker(user_role_changed) as tracker:
                auth_service.change_role(user_id=user_id, role="admin")
                assert tracker.called
            user.delete()

    def test_article_published_emits_signal(self, app, signal_tracker):
        article_service = get_article_service()
        with app.app_context():
            author = User(username="evt_auth", email="evt@test.com", role="admin")
            author.set_password("password")
            author.save()
            user_identity = UserIdentity(
                id=str(author.id),
                username=author.username,
                role=author.role,
                token_version=0,
            )
            draft_art = article_service.create_article(
                article_dto=ArticleCreateUpdate(
                    title="Draft", content="C", summary="S", is_published=False
                ),
                user=user_identity,
            )
            article_id = str(draft_art.id)
            with signal_tracker(article_published) as tracker:
                article_service.update_article(
                    article_id=article_id,
                    article_dto=ArticleCreateUpdate(
                        title="Pub", content="C", summary="S", is_published=True
                    ),
                    user=user_identity,
                )
                assert tracker.called
            author.delete()
