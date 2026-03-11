import os
import pytest
import re
from playwright.sync_api import Page, expect

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": True}

def is_horizontally_scrollable(page: Page):
    """
    Checks if the page has a horizontal scrollbar.
    """
    return page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")

@pytest.mark.e2e
def test_mobile_hamburger_menu(page: Page):
    """
    Verifies that the hamburger menu appears and functions on mobile devices.
    """
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:5000")
    
    # Set viewport to iPhone 12 size
    page.set_viewport_size({"width": 390, "height": 844})
    
    page.goto(f"{base_url}/home")
    
    # Handle Cookie Consent if visible
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    # 1. Verify hamburger menu button is visible
    nav_toggle = page.locator(".nav-toggle")
    expect(nav_toggle).to_be_visible()
    
    # 2. Verify nav list is hidden initially
    nav_list = page.locator(".nav-list")
    expect(nav_list).not_to_be_visible()
    
    # 3. Open menu
    nav_toggle.click()
    expect(nav_list).to_be_visible()
    expect(nav_list).to_have_class(re.compile(r"is-open"))
    
    # 4. Click a link in the menu (e.g., Blog)
    blog_link = nav_list.locator("text=Blog")
    blog_link.click()
    
    # 5. Verify navigation occurred
    expect(page).to_have_url(re.compile(r"/blog"))
    expect(page.locator("[data-test='view-articles']")).to_be_visible()

@pytest.mark.e2e
def test_mobile_overflow_and_layout(page: Page):
    """
    Checks for horizontal overflow and element clipping on various mobile sizes.
    """
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:5000")
    
    viewports = [
        {"width": 320, "height": 568},  # iPhone 5/SE
        {"width": 375, "height": 667},  # iPhone 6/7/8
        {"width": 414, "height": 896},  # iPhone XR/XS Max
    ]
    
    for vp in viewports:
        page.set_viewport_size(vp)
        page.goto(f"{base_url}/home")
        
        # Handle Cookie Consent if visible
        accept_btn = page.locator("[data-test='cookie-accept']")
        if accept_btn.is_visible():
            accept_btn.click()

        # 1. Check for horizontal overflow
        assert not is_horizontally_scrollable(page), f"Page is horizontally scrollable at {vp['width']}px"
        
        # 2. Verify Hero Card fits (should not be wider than viewport)
        hero_card = page.locator(".hero-card")
        box = hero_card.bounding_box()
        assert box["width"] <= vp["width"], f"Hero card is wider than viewport at {vp['width']}px"
        
        # 3. Verify main content visibility
        expect(page.locator("[data-test='profile-name']")).to_be_visible()
        expect(page.locator("[data-test='profile-statement']")).to_be_visible()

@pytest.mark.e2e
def test_mobile_scroll_resilience(page: Page):
    """
    Verifies that the page remains scrollable and doesn't exhibit "bad scroll"
    (e.g., sticking, jumping, or locking) on mobile.
    """
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:5000")
    page.set_viewport_size({"width": 375, "height": 667})
    
    page.goto(f"{base_url}/home")
    
    # Handle Cookie Consent if visible
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    # 1. Ensure vertical scroll is possible
    total_height = page.evaluate("document.body.scrollHeight")
    viewport_height = page.viewport_size["height"]
    
    if total_height > viewport_height:
        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        current_scroll = page.evaluate("window.scrollY")
        assert current_scroll > 0, "Vertical scroll failed"
        
        # Scroll back up
        page.evaluate("window.scrollTo(0, 0)")
        current_scroll = page.evaluate("window.scrollY")
        assert current_scroll == 0, "Failed to scroll back to top"
    
    # 2. Check for overflow-x on body/html (redundant but explicit)
    overflow_x = page.evaluate("window.getComputedStyle(document.body).overflowX")
    assert overflow_x in ["hidden", "visible", "auto"], f"Unexpected overflow-x: {overflow_x}"
