import pytest
from src.models.post import Post
from src.models.user import User
import datetime

@pytest.fixture
def test_user(app):
    user = User(username='testuser', email='test@example.com', role='user')
    user.set_password('Password123')
    user.save()
    yield user
    user.delete()

class TestHtmlSanitization:
    """Tests for HTML sanitization in Post content and summary."""

    def test_malicious_script_tag_removed(self, app, test_user):
        """Ensure <script> tags are removed from content and summary."""
        with app.app_context():
            malicious_content = "Hello <script>alert('xss')</script> World!"
            post = Post(
                title="XSS Test",
                slug="xss-test",
                content=malicious_content,
                summary=malicious_content,
                author=test_user,
                is_published=True,
                publication_date=datetime.datetime.now(datetime.UTC)
            )
            post.save()
            
            # Retrieve the post to ensure sanitization persisted
            retrieved_post = Post.objects(slug="xss-test").first()
            assert retrieved_post is not None
            assert "<script>" not in retrieved_post.content
            assert retrieved_post.content == "Hello alert('xss') World!" # Content should remain
            assert "<script>" not in retrieved_post.summary
            assert retrieved_post.summary == "Hello alert('xss') World!" # Content should remain
            
            retrieved_post.delete()

    def test_allowed_html_tags_preserved(self, app, test_user):
        """Ensure allowed HTML tags are preserved in content and summary."""
        with app.app_context():
            allowed_html = "This is a <b>bold</b> and <i>italic</i> text with a <a href='http://example.com'>link</a>."
            post = Post(
                title="Allowed HTML Test",
                slug="allowed-html-test",
                content=allowed_html,
                summary=allowed_html,
                author=test_user,
                is_published=True,
                publication_date=datetime.datetime.now(datetime.UTC)
            )
            post.save()

            retrieved_post = Post.objects(slug="allowed-html-test").first()
            assert retrieved_post is not None
            assert "<b>bold</b>" in retrieved_post.content
            assert "<i>italic</i>" in retrieved_post.content
            assert "<a href=\"http://example.com\">link</a>" in retrieved_post.content # bleach might normalize quotes
            assert "<b>bold</b>" in retrieved_post.summary
            assert "<i>italic</i>" in retrieved_post.summary
            assert "<a href=\"http://example.com\">link</a>" in retrieved_post.summary
            
            retrieved_post.delete()

    def test_disallowed_html_tags_removed(self, app, test_user):
        """Ensure disallowed HTML tags are removed from content and summary."""
        with app.app_context():
            disallowed_html = "Text with <form action='.'>form</form> and <input type='text'>."
            post = Post(
                title="Disallowed HTML Test",
                slug="disallowed-html-test",
                content=disallowed_html,
                summary=disallowed_html,
                author=test_user,
                is_published=True,
                publication_date=datetime.datetime.now(datetime.UTC)
            )
            post.save()

            retrieved_post = Post.objects(slug="disallowed-html-test").first()
            assert retrieved_post is not None
            assert "<form>" not in retrieved_post.content
            assert "<input>" not in retrieved_post.content
            assert "form" in retrieved_post.content # Text content should remain
            assert "Text with form and ." == retrieved_post.content # Ensure only tags are stripped
            assert "<form>" not in retrieved_post.summary
            assert "<input>" not in retrieved_post.summary
            assert "Text with form and ." == retrieved_post.summary
            
            retrieved_post.delete()

    def test_disallowed_attributes_removed(self, app, test_user):
        """Ensure disallowed attributes are removed from allowed tags."""
        with app.app_context():
            html_with_disallowed_attr = "<a href='http://example.com' onclick='alert(1)'>Click me</a>"
            post = Post(
                title="Disallowed Attr Test",
                slug="disallowed-attr-test",
                content=html_with_disallowed_attr,
                summary=html_with_disallowed_attr,
                author=test_user,
                is_published=True,
                publication_date=datetime.datetime.now(datetime.UTC)
            )
            post.save()

            retrieved_post = Post.objects(slug="disallowed-attr-test").first()
            assert retrieved_post is not None
            assert "onclick" not in retrieved_post.content
            assert "<a href=\"http://example.com\">Click me</a>" in retrieved_post.content
            assert "onclick" not in retrieved_post.summary
            assert "<a href=\"http://example.com\">Click me</a>" in retrieved_post.summary
            
            retrieved_post.delete()
