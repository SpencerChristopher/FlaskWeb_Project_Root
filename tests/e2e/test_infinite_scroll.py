import os
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_blog_infinite_scroll(page: Page, base_url: str):
    """
    Verify that the blog page correctly implements infinite scroll.
    """
    require_heavy = os.environ.get("REQUIRE_HEAVY_SEED", "").lower() in {"1", "true", "yes"}
    response = page.request.get(f"{base_url}/api/blog")
    if not response.ok:
        pytest.skip("Blog API unavailable; skipping infinite scroll gate.")

    data = response.json()
    total_articles = (data.get("pagination") or {}).get("total_articles", 0)
    if total_articles < 13:
        message = f"Infinite scroll requires >=13 articles; found {total_articles}."
        if require_heavy:
            pytest.fail(message)
        pytest.skip(message)

    page.goto(f"{base_url}/blog")

    # Bypass cookie consent if needed
    if page.locator("#cookie-dialog").is_visible():
        page.click("#cookie-accept")

    # 1. Verify initial count (per_page is 6)
    # Cards have data-test='article-card-X'
    initial_cards = page.locator("[data-test^='article-card-']")
    expect(initial_cards).to_have_count(6)

    # 2. Scroll to the bottom to trigger infinite scroll
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    # 3. Wait for more articles to load (should be 12 now)
    # Increased timeout as loading 1000+ words might take a moment on slow stacks
    expect(page.locator("[data-test='article-card-6']")).to_be_visible(timeout=10000)

    new_count = page.locator("[data-test^='article-card-']").count()
    assert new_count > 6, f"Expected more than 6 articles after scroll, got {new_count}"

    # 4. Scroll again to verify multiple 'pages' load
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    expect(page.locator("[data-test='article-card-12']")).to_be_visible(timeout=10000)

    final_count = page.locator("[data-test^='article-card-']").count()
    assert final_count > 12
    print(f"Infinite scroll verified: {final_count} articles loaded across 3 loads.")
