from src.models.article import Article


def test_orphan_article_blocks_non_admin_access(client, app, content_admin_headers):
    """
    Ensure orphaned articles (missing author) do not cause 500s for non-admins.
    Expected: 404 Not Found to avoid leaking existence.
    """
    with app.app_context():
        # Insert a legacy/orphaned document without an author field.
        raw_doc = {
            "title": "Orphan Article",
            "slug": "orphan-article",
            "content": "Content",
            "summary": "Summary",
            "is_published": True,
        }
        inserted_id = Article._get_collection().insert_one(raw_doc).inserted_id
        article_id = str(inserted_id)

    resp = client.get(
        f"/api/content/articles/{article_id}", headers=content_admin_headers
    )
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error_code"] == "NOT_FOUND"
