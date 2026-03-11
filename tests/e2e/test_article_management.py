import os
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": True}


@pytest.mark.e2e
def test_article_lifecycle_admin(page: Page):
    """
    Test the full lifecycle of an article: Create, Edit, Publish, Delete.
    """
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:5000")
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "NewAdmin2020!")

    # 1. Login
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(f"{base_url}/login")

    # Accept cookies
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    page.fill("#username", admin_user)
    page.fill("#password", admin_pass)
    page.click("button[type='submit']")

    # Wait for login to complete
    page.wait_for_selector("[data-test='view-home']")

    # 2. Navigate to Content Manager
    page.click("text=Manage Articles")
    page.wait_for_selector("[data-test='view-content-manager']")

    # Clear existing test article if it exists
    title = "E2E Test Article"
    existing_row = page.locator(f"tr:has-text('{title}')")
    if existing_row.count() > 0:
        page.once("dialog", lambda dialog: dialog.accept())
        existing_row.locator(".delete-article-btn").click()
        page.wait_for_selector(f"tr:has-text('{title}')", state="hidden")

    # 3. Create a New Article
    # Expected: Clicking 'New Article' should open a form or modal
    page.click("[data-test='create-article']")

    # Check if form elements exist (this will likely fail currently)
    expect(page.locator("#article-form-modal")).to_be_visible()

    title = "E2E Test Article"
    summary = "Summary of the test article."
    content = "Detailed content for the E2E test article."

    page.fill("#a-title", title)
    page.fill("#a-summary", summary)
    page.fill("#a-content", content)

    # Save as Draft first
    page.click("#save-article-btn")

    # Verify it appears in the table
    page.wait_for_selector(f"tr:has-text('{title}')")
    status_badge = page.locator(f"tr:has-text('{title}') .badge")
    expect(status_badge).to_have_text("Draft")

    # 4. Edit and Publish
    page.locator(f"tr:has-text('{title}') .edit-article-btn").click()
    expect(page.locator("#article-form-modal")).to_be_visible()

    # Check 'Published' checkbox
    page.check("#a-published")
    page.click("#save-article-btn")

    # Verify status changed
    page.wait_for_selector(f"tr:has-text('{title}')")
    expect(page.locator(f"tr:has-text('{title}') .badge")).to_have_text("Published")

    # 5. Verify on Public Blog
    page.goto(f"{base_url}/blog")
    expect(page.locator(f"h3:has-text('{title}')")).to_be_visible()

    # 6. Delete Article
    page.goto(f"{base_url}/admin/articles")
    page.wait_for_selector(f"tr:has-text('{title}')")

    # Handle delete confirmation
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator(f"tr:has-text('{title}') .delete-article-btn").click()

    # Verify it's gone
    expect(page.locator(f"tr:has-text('{title}')")).not_to_be_visible()
