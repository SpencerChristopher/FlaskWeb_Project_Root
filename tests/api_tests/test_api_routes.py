import pytest
from src.models.article import Article

class TestApiRoutes:
    def test_home_api_returns_expected_structure(self, client):
        response = client.get('/api/home')
        assert response.status_code == 200
        data = response.get_json()
        assert 'title' in data

    def test_blog_list_api_successful(self, app, client):
        with app.app_context():
            from src.models.user import User
            author = User.objects.first()
            if not author:
                author = User(username="blog_author", email="blog@test.com", role="admin")
                author.set_password("password")
                author.save()

            Article(
                title="Test Blog Article",
                slug="test-blog-article",
                content="Content",
                summary="Summary",
                author=author,
                is_published=True
            ).save()

        response = client.get('/api/blog')
        assert response.status_code == 200
        data = response.get_json()
        assert 'posts' in data
        assert len(data['posts']) >= 1

    def test_blog_article_api_successful(self, app, client):
        with app.app_context():
            from src.models.user import User
            author = User.objects.first()
            Article(
                title="Detail Article",
                slug="detail-article",
                content="Content",
                summary="Summary",
                author=author,
                is_published=True
            ).save()

        response = client.get('/api/blog/detail-article')
        assert response.status_code == 200
        assert response.get_json()['title'] == "Detail Article"
