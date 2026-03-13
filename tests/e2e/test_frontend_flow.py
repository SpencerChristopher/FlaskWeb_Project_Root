import os
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_path_based_routing_home(page: Page, base_url: str):
    """
    Verifies that the HomeView is accessible via a path-based URL (/home).
    """
    # Navigating directly to /home should work with History API
    page.goto(f"{base_url}/home")

    # Handle Cookie Consent if visible
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    # Hero card should be visible
    hero = page.locator("[data-test='view-home'] .hero-card")
    expect(hero).to_be_visible()

    # URL should stay at /home (no #)
    expect(page).to_have_url(f"{base_url}/home")


@pytest.mark.e2e
def test_article_navigation_flow_paths(page: Page, base_url: str):
    """
    Verifies navigation using the History API (path-based) for the blog flow.
    """
    # Go to blog via path
    page.goto(f"{base_url}/blog")

    # Handle Cookie Consent if visible
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    # Click first article (link should be path-based)
    first_article_link = page.locator("[data-test^='article-card-'] a").first
    expect(first_article_link).to_be_visible()

    # Verify the href is NOT a hash
    href = first_article_link.get_attribute("href")
    assert not href.startswith("#")

    import re

    first_article_link.click()

    # Verify we are on detail page path (dynamic slug)
    expect(page).to_have_url(re.compile(f"{base_url}/blog/.+"))
    expect(page.locator("[data-test='view-article-detail']")).to_be_visible()

    # Click "Back to Blog" button
    back_btn = page.locator("text=Back to Blog")
    expect(back_btn).to_be_visible()
    back_btn.click()

    # Verify we are back on /blog
    expect(page).to_have_url(f"{base_url}/blog")
    expect(page.locator("[data-test='view-articles']")).to_be_visible()
