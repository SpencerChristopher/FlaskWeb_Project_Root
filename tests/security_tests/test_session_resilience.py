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
def test_silent_refresh_interceptor(page: Page):
    """
    Verifies that the frontend can recover from an expired access token
    silently without redirecting the user to login or home.
    """
    base_url = os.getenv("E2E_BASE_URL", "https://localhost")
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "NewAdmin2020!")

    # 1. Login
    page.goto(f"{base_url}#login")
    
    # Accept cookies
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    page.fill("#username", admin_user)
    page.fill("#password", admin_pass)
    page.click("button[type='submit']")

    # Wait for login to complete and stay on Home
    page.wait_for_selector("[data-test='view-home']")
    
    # 2. Simulate Token Expiry
    # We trigger a special debug endpoint or manually delete the access cookie
    # Since we can't easily delete HttpOnly cookies via JS, 
    # we'll use a known trick: the interceptor should catch a 401.
    
    # Instead of deleting, we'll navigate to a page that triggers an API call,
    # and we'll intercept the network request to force a 401 ONCE.
    
    def handle_route(route):
        # Check if this is the first attempt (no X-Is-Retry header)
        if "/api/content/profile" in route.request.url and not route.request.headers.get("x-is-retry"):
            # Force a 401 for the first attempt
            route.fulfill(
                status=401,
                content_type="application/json",
                body='{"message": "Token expired", "error_code": "TOKEN_EXPIRED"}'
            )
        else:
            route.continue_()

    # Navigate to profile edit (triggers a GET /api/content/profile)
    # We want to see if it RECOVERS and stays on the page.
    page.route("**/api/content/profile", handle_route)
    
    # Trigger navigation to profile
    page.click("text=Edit Profile")
    
    # Expectation: The page should eventually load the Profile view 
    # even though the first request was a 401.
    page.wait_for_selector("[data-test='view-profile']")
    
    # Verify we are NOT on the login page or home page
    expect(page).not_to_have_url(f"{base_url}#login")
    expect(page.locator("[data-test='view-profile']")).to_be_visible()
