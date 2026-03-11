import os
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": True}

@pytest.mark.e2e
def test_guest_cold_start_source_protection(page: Page):
    """
    Gate: Guest users should not download Admin View source code on initial load.
    Verifies that 'ProfileView.js' and 'ContentManagerView.js' are not in the network logs.
    """
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:5000")
    
    # Start monitoring network requests
    admin_module_requests = []
    page.on("request", lambda request: admin_module_requests.append(request.url) 
            if ("ProfileView.js" in request.url or "ContentManagerView.js" in request.url) else None)

    # 1. Cold Start on Home Page
    page.goto(f"{base_url}/home")
    
    # Handle Cookie Consent if it appears (blocking init)
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()
    
    # Wait for app.js to finish loading and initializing
    page.wait_for_selector("[data-test='view-home']")
    
    # Assertion: No Admin modules should be loaded
    assert len(admin_module_requests) == 0, f"Security Leak: Admin modules loaded for Guest: {admin_module_requests}"

@pytest.mark.e2e
def test_admin_lazy_load_on_navigation(page: Page):
    """
    Gate: Admin modules should only be downloaded when navigating to protected routes.
    """
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:5000")
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "NewAdmin2020!")

    # Start monitoring
    admin_module_requests = []
    page.on("request", lambda request: admin_module_requests.append(request.url) 
            if ("ProfileView.js" in request.url) else None)

    # 1. Login and stay on home
    page.goto(f"{base_url}/login")
    
    # Accept cookies
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    page.fill("#username", admin_user)
    page.fill("#password", admin_pass)
    page.click("button[type='submit']")
    page.wait_for_selector("[data-test='view-home']")
    
    # Assertion: ProfileView should still not be loaded on Home even if logged in
    assert len(admin_module_requests) == 0, "Security Leak: ProfileView loaded before navigation"

    # 2. Navigate to Profile
    page.click("nav #mainNavList >> text=Edit Profile")
    page.wait_for_selector("[data-test='view-admin-profile']")
    
    # Assertion: ProfileView should NOW be loaded
    assert len(admin_module_requests) == 1, "Failure: ProfileView was not lazy-loaded on navigation"
