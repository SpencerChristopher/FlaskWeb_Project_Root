import os
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": True}


@pytest.mark.e2e
def test_guest_navigation_from_login(page: Page):
    """Verifies a guest can navigate away from the login page."""
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:5000")

    # Go to Login
    page.goto(f"{base_url}/login")

    # Accept cookies
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    expect(page.locator("[data-test='view-login']")).to_be_visible()

    # Try to go to Home
    page.click("nav #mainNavList >> text=Home")
    expect(page).to_have_url(f"{base_url}/home")
    expect(page.locator("[data-test='view-home']")).to_be_visible()

    # Go back to Login
    page.click("nav #mainNavList >> text=Admin")
    expect(page).to_have_url(f"{base_url}/login")

    # Try to go to Blog
    page.click("nav #mainNavList >> text=Blog")
    expect(page).to_have_url(f"{base_url}/blog")
    expect(page.locator("[data-test='view-articles']")).to_be_visible()


@pytest.mark.e2e
def test_admin_navigation_after_login(page: Page):
    """Verifies an admin can navigate after logging in."""
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:5000")
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "NewAdmin2020!")

    # 1. Login
    page.goto(f"{base_url}/login")

    # Accept cookies
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    page.fill("#username", admin_user)
    page.fill("#password", admin_pass)
    page.click("button[type='submit']")

    # Should land on Home
    page.wait_for_selector("[data-test='view-home']")
    expect(page).to_have_url(f"{base_url}/home")

    # 2. Go to Edit Profile (from Nav)
    page.click("nav #mainNavList >> text=Edit Profile")
    expect(page).to_have_url(f"{base_url}/admin/profile")
    expect(page.locator("[data-test='view-admin-profile']")).to_be_visible()

    # 3. Go to Manage Articles (from Nav)
    page.click("nav #mainNavList >> text=Manage Articles")
    expect(page).to_have_url(f"{base_url}/admin/articles")
    expect(page.locator("[data-test='view-content-manager']")).to_be_visible()

    # 4. Go back to Home
    page.click("nav #mainNavList >> text=Home")
    expect(page).to_have_url(f"{base_url}/home")
