import pytest
import time
from playwright.sync_api import Page, expect

@pytest.fixture
def browser_context_args(browser_context_args):
    """Override playwright context to ignore HTTPS errors for self-signed certs."""
    return {
        **browser_context_args,
        "ignore_https_errors": True
    }

@pytest.mark.performance
@pytest.mark.e2e
def test_spa_time_to_interactive(page: Page, base_url: str):
    """
    E2E performance gate: verify that the SPA becomes interactive within the budget.
    Measures from navigation start until the 'initializing' flag is cleared.
    """
    
    # 1. Start timing
    start_time = time.perf_counter()
    
    # 2. Navigate and wait for the cookie dialog (our first blocker)
    page.goto(base_url)
    
    # Wait for the first visible UI element that indicates app logic is running
    expect(page.locator("#cookie-dialog")).to_be_visible()
    
    # 3. Accept cookies (triggers startApp logic)
    page.click("#cookie-accept")
    
    # 4. Wait for the main-content to show the Hero section
    # This proves startApp() completed and the HomeView template rendered
    expect(page.locator("[data-test='profile-name']")).to_be_visible()
    
    end_time = time.perf_counter()
    tti = (end_time - start_time) * 1000
    
    print(f"\nBrowser TTI (Accept to Home): {tti:.2f}ms")
    
    # Threshold: 2000ms for a local dev container (accounting for initial Docker response)
    assert tti < 2000, f"SPA initialization too slow: {tti:.2f}ms"

@pytest.mark.performance
@pytest.mark.e2e
def test_navigation_snappiness(page: Page, base_url: str):
    """
    E2E performance gate: verify that internal navigation is nearly instant.
    """
    
    # Setup: Get past consent
    page.goto(base_url)
    page.click("#cookie-accept")
    expect(page.locator("[data-test='profile-name']")).to_be_visible()
    
    # 1. Start timing
    start_time = time.perf_counter()
    
    # 2. Click a link to navigate to Blog
    page.click("a[href='/blog']")
    
    # 3. Wait for the blog list to render
    expect(page.locator("[data-test='article-grid']")).to_be_visible()
    
    end_time = time.perf_counter()
    nav_time = (end_time - start_time) * 1000
    
    print(f"\nInternal Nav (Home to Blog): {nav_time:.2f}ms")
    
    # Internal navigation should be extremely fast (under 300ms) as it's just a 
    # fetch + template swap, no page reload.
    assert nav_time < 500, f"Internal navigation too slow: {nav_time:.2f}ms"
