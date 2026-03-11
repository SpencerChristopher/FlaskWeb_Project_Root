import os
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_ui_consistency_factory_gate(page: Page):
    """
    Verifies that cards in both Home and Blog views share the same
    foundational styling (the 'Factory' requirement).
    """
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:5000")

    # 1. Check Experience Cards on Home
    page.goto(f"{base_url}/home")

    # Accept cookies
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    # Wait for the view to render
    page.wait_for_selector("[data-test^='work-card-']")
    first_exp_card = page.locator("[data-test^='work-card-']").first

    # Core styling requirements
    expect(first_exp_card).to_have_class(compile_regex(r"card.*shadow-sm.*bg-white"))

    # 2. Check Blog Cards on Blog
    page.goto(f"{base_url}/blog")
    page.wait_for_selector("[data-test^='article-card-']")
    first_blog_card = page.locator("[data-test^='article-card-']").first

    # Core styling requirements should match Experience Cards
    expect(first_blog_card).to_have_class(compile_regex(r"card.*shadow-sm.*bg-white"))


@pytest.mark.e2e
def test_reactive_state_observer_gate(page: Page):
    """
    Verifies that logging in updates MULTIPLE areas of the UI
    (the 'Observer' requirement).
    """
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:5000")
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "NewAdmin2020!")

    page.goto(f"{base_url}/login")

    # Accept cookies
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    # Before login, verify 'Edit Profile' is NOT in the navbar and NOT in the hero (if on home)
    page.goto(f"{base_url}/home")
    expect(page.locator("nav >> text=Edit Profile")).not_to_be_visible()
    expect(page.locator(".hero-card >> text=Edit Profile")).not_to_be_visible()

    # Perform Login
    page.goto(f"{base_url}/login")
    page.fill("#username", admin_user)
    page.fill("#password", admin_pass)
    page.click("button[type='submit']")

    # After login, the 'Observer' should have triggered updates in both Nav and Home Hero
    page.wait_for_selector("[data-test='view-home']")

    # Check Navbar (Observer update 1)
    expect(page.locator("nav >> text=Edit Profile")).to_be_visible()

    # Check Hero (Observer update 2)
    expect(page.locator(".hero-card >> text=Edit Profile")).to_be_visible()


def compile_regex(pattern):
    import re

    return re.compile(pattern)
