import pytest
from src.models.user import User
from src.models.post import Post
from flask_jwt_extended import create_access_token
import datetime

# Fixture to create an admin user in the database
@pytest.fixture
def test_admin_user(app):
    with app.app_context():
        admin_user = User(username='adminuser', email='admin@example.com', role='admin')
        admin_user.set_password('AdminPassword123')
        admin_user.save()
        yield admin_user
        admin_user.delete()



# Helper to get admin headers
@pytest.fixture
def admin_headers(login_user_fixture, test_admin_user):
    token = login_user_fixture('adminuser', 'AdminPassword123')
    return {'Authorization': f'Bearer {token}'}

class TestAdminPostRoutes:
    """Tests for admin post management routes."""

    def test_get_post_with_invalid_id_format(self, client, admin_headers):
        """
        Tests that getting a post with an invalid ID format returns a 400 Bad Request.
        This test expects the backend to validate ObjectId format.
        """
        invalid_id = "not-a-valid-objectid"
        response = client.get(f'/api/admin/posts/{invalid_id}', headers=admin_headers)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    def test_update_post_with_invalid_id_format(self, client, admin_headers):
        """
        Tests that updating a post with an invalid ID format returns a 400 Bad Request.
        """
        invalid_id = "another-invalid-id"
        payload = {
            "title": "Updated Title",
            "content": "Updated Content",
            "summary": "Updated Summary",
            "is_published": True
        }
        response = client.put(f'/api/admin/posts/{invalid_id}', headers=admin_headers, json=payload)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    def test_delete_post_with_invalid_id_format(self, client, admin_headers):
        """
        Tests that deleting a post with an invalid ID format returns a 400 Bad Request.
        """
        invalid_id = "yet-another-invalid-id"
        response = client.delete(f'/api/admin/posts/{invalid_id}', headers=admin_headers)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    def test_get_post_with_nosql_injection_id(self, client, admin_headers):
        """
        Tests that getting a post with a NoSQL injection payload in the ID returns a 400 Bad Request.
        """
        nosql_injection_id = "{'$ne': 'some_value'}" # Example NoSQL injection payload
        response = client.get(f'/api/admin/posts/{nosql_injection_id}', headers=admin_headers)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    def test_update_post_with_nosql_injection_id(self, client, admin_headers):
        """
        Tests that updating a post with a NoSQL injection payload in the ID returns a 400 Bad Request.
        """
        nosql_injection_id = "{'$gt': ''}" # Another example NoSQL injection payload
        payload = {
            "title": "Updated Title",
            "content": "Updated Content",
            "summary": "Updated Summary",
            "is_published": True
        }
        response = client.put(f'/api/admin/posts/{nosql_injection_id}', headers=admin_headers, json=payload)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    def test_delete_post_with_nosql_injection_id(self, client, admin_headers):
        """
        Tests that deleting a post with a NoSQL injection payload in the ID returns a 400 Bad Request.
        """
        nosql_injection_id = "{'$where': '1 = 1'}" # Yet another example
        response = client.delete(f'/api/admin/posts/{nosql_injection_id}', headers=admin_headers)
        assert response.status_code == 400
        assert response.json['error_code'] == 'BAD_REQUEST'
        assert 'Validation error' in response.json['message']
        assert isinstance(response.json['details'], list)
        assert len(response.json['details']) == 1
        assert response.json['details'][0]['loc'] == []
        assert 'is not a valid ObjectId' in response.json['details'][0]['msg']

    # You would also have tests for valid admin post operations here (create, get, update, delete)
    # For brevity, I'm only adding the new validation tests.

    def test_create_post_successful(self, client, admin_headers, test_admin_user):
        """Tests successful creation of a new post."""
        payload = {
            "title": "My New Test Post",
            "slug": "my-new-test-post",
            "content": "This is the content of my new test post.",
            "summary": "Summary of my new test post.",
            "is_published": True
        }
        response = client.post('/api/admin/posts', headers=admin_headers, json=payload)
        assert response.status_code == 201
        assert response.json['message'] == 'Post created successfully'
        assert 'id' in response.json
        assert response.json['title'] == payload['title']
        assert response.json['slug'] == payload['slug']
        assert response.json['content'] == payload['content']
        assert response.json['summary'] == payload['summary']
        assert response.json['is_published'] == payload['is_published']
        assert response.json['author']['username'] == test_admin_user.username

        # Verify post exists in DB
        with client.application.app_context():
            post = Post.objects(slug=payload['slug']).first()
            assert post is not None
            assert post.title == payload['title']
            post.delete() # Clean up

    def test_get_post_successful(self, client, admin_headers, test_admin_user):
        """Tests successful retrieval of an existing post."""
        with client.application.app_context():
            post = Post(
                title="Existing Post",
                slug="existing-post",
                content="Content of existing post.",
                summary="Summary of existing post.",
                author=test_admin_user,
                is_published=True
            )
            post.save()
            post_id = str(post.id)

        response = client.get(f'/api/admin/posts/{post_id}', headers=admin_headers)
        assert response.status_code == 200
        assert response.json['title'] == post.title
        assert response.json['slug'] == post.slug
        assert response.json['content'] == post.content
        assert response.json['summary'] == post.summary
        assert response.json['is_published'] == post.is_published
        assert response.json['author']['username'] == test_admin_user.username

        with client.application.app_context():
            post.delete() # Clean up

    def test_update_post_successful(self, client, admin_headers, test_admin_user):
        """Tests successful update of an existing post."""
        with client.application.app_context():
            post = Post(
                title="Post to Update",
                slug="post-to-update",
                content="Original content.",
                summary="Original summary.",
                author=test_admin_user,
                is_published=False
            )
            post.save()
            post_id = str(post.id)

        updated_payload = {
            "title": "Updated Post Title",
            "content": "Updated content for the post.",
            "summary": "Updated summary for the post.",
            "is_published": True
        }
        response = client.put(f'/api/admin/posts/{post_id}', headers=admin_headers, json=updated_payload)
        assert response.status_code == 200
        assert response.json['message'] == 'Post updated successfully'
        assert response.json['title'] == updated_payload['title']
        assert response.json['content'] == updated_payload['content']
        assert response.json['summary'] == updated_payload['summary']
        assert response.json['is_published'] == updated_payload['is_published']

        # Verify changes in DB
        with client.application.app_context():
            updated_post = Post.objects(id=post_id).first()
            assert updated_post.title == updated_payload['title']
            assert updated_post.content == updated_payload['content']
            assert updated_post.summary == updated_payload['summary']
            assert updated_post.is_published == updated_payload['is_published']
            updated_post.delete() # Clean up

    def test_delete_post_successful(self, client, admin_headers, test_admin_user):
        """Tests successful deletion of an existing post."""
        with client.application.app_context():
            post = Post(
                title="Post to Delete",
                slug="post-to-delete",
                content="Content to delete.",
                summary="Summary to delete.",
                author=test_admin_user,
                is_published=True
            )
            post.save()
            post_id = str(post.id)

        response = client.delete(f'/api/admin/posts/{post_id}', headers=admin_headers)
        assert response.status_code == 200
        assert response.json['message'] == 'Post deleted successfully'

        # Verify post is deleted from DB
        with client.application.app_context():
            deleted_post = Post.objects(id=post_id).first()
            assert deleted_post is None
