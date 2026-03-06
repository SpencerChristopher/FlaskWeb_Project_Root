import os
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "ignore_https_errors": True
    }

@pytest.mark.e2e
def test_responsive_layout_home(page: Page):
    """
    Verifies that the HomeView layout adapts to mobile and desktop viewports.
    """
    base_url = os.getenv("E2E_BASE_URL", "https://localhost")
    
    # 1. Test Desktop View
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(base_url)
    
    # Handle Cookie Consent if visible
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()
    
    # Hero card should be visible and wide
    hero = page.locator("[data-test='view-home'] .hero-card")
    expect(hero).to_be_visible()
    
    # 2. Test Mobile View
    page.set_viewport_size({"width": 375, "height": 667}) # iPhone SE size
    page.goto(base_url)
    
    # Nav list should be hidden by default on mobile (behind burger menu)
    nav_list = page.locator("#mainNavList")
    expect(nav_list).not_to_be_visible()
    
    # Burger menu button should be visible
    nav_toggle = page.locator("#navToggle")
    expect(nav_toggle).to_be_visible()
    
    # Clicking toggle should show nav
    nav_toggle.click()
    expect(nav_list).to_be_visible()

@pytest.mark.e2e
def test_article_navigation_flow(page: Page):
    """
    Verifies that the "Back to Blog" navigation added in the last step works.
    """
    base_url = os.getenv("E2E_BASE_URL", "https://localhost")
    
    # Go to blog
    page.goto(f"{base_url}#blog")

    # Handle Cookie Consent if visible
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()
    
    # Click first article
    first_article = page.locator("[data-test^='article-card-']").first
    expect(first_article).to_be_visible()
    first_article.locator("a").click()
    
    # Verify we are on detail page
    expect(page.locator("[data-test='view-article-detail']")).to_be_visible()
    
    # Click "Back to Blog" button
    back_btn = page.locator("text=Back to Blog")
    expect(back_btn).to_be_visible()
    back_btn.click()
    
    # Verify we are back on the blog list
    expect(page.locator("[data-test='view-articles']")).to_be_visible()
