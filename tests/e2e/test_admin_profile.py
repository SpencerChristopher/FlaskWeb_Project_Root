import os
import pytest
import re
from playwright.sync_api import Page, expect

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "ignore_https_errors": True
    }

@pytest.mark.e2e
def test_admin_profile_workflow(page: Page):
    """
    Test the logged-in admin experience for editing the profile.
    Verifies the new work history list/modal UI on a desktop viewport.
    """
    base_url = os.getenv("E2E_BASE_URL", "https://localhost")
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

    # Wait for login to complete and show home view
    page.wait_for_selector("[data-test='view-home']")
    
    # 2. Navigate to Edit Profile
    # Use the link from the nav to ensure it works
    page.click("text=Edit Profile")
    page.wait_for_selector("[data-test='view-admin-profile']")
    expect(page.locator("h1:has-text('Edit Profile')")).to_be_visible()

    # Clear existing work history to ensure clean test state
    delete_btns = page.locator(".remove-work-btn")
    count = delete_btns.count()
    for i in range(count):
        # Always click the first one as they shift
        page.once("dialog", lambda dialog: dialog.accept())
        delete_btns.first.click()

    # 3. Test Headline Role and Override Logic
    # Set a headline
    page.fill("#p-headline", "Manual Headline Role")
    
    # Ensure no 'Present' jobs exist for this part of the test (clear list if needed or just add ended one)
    # For simplicity, we just add a job that ended
    page.click("#open-add-work-modal")
    page.fill("#w-company", "Old Corp")
    page.fill("#w-role", "Legacy Developer")
    page.fill("#w-start", "2020-01")
    page.fill("#w-end", "2023-01") # Ended
    page.fill("#w-location", "London")
    page.click("#save-work-entry")
    
    page.click("button[type='submit']") # Save Profile
    page.wait_for_selector("[data-test='view-home']")
    
    # Hero should show the Manual Headline because no active job exists
    expect(page.locator(".role-title")).to_have_text("Manual Headline Role")

    # Now add a 'Present' job to test override
    page.click("text=Edit Profile")
    page.click("#open-add-work-modal")
    page.fill("#w-company", "Active Corp")
    page.fill("#w-role", "Override Role")
    page.fill("#w-start", "2024-01")
    page.fill("#w-end", "Present") # Active
    page.fill("#w-location", "Remote")
    page.click("#save-work-entry")
    
    page.click("button[type='submit']")
    page.wait_for_selector("[data-test='view-home']")
    
    # Hero should now show 'Override Role' instead of 'Manual Headline'
    expect(page.locator(".role-title")).to_have_text("Override Role")

    # 4. Verify Work History UI substantial cards
    page.click("text=Edit Profile")
    page.wait_for_selector("[data-test='view-admin-profile']")
    
    add_btn = page.locator("#open-add-work-modal")
    expect(add_btn).to_be_visible()
    expect(add_btn).to_have_text("+ Add Experience")

    # 4. Open Modal and add a new entry
    add_btn.click()
    expect(page.locator("#work-modal")).to_be_visible()
    
    page.fill("#w-company", "E2E Test Corp")
    page.fill("#w-role", "Desktop UI Tester")
    page.fill("#w-start", "2024-01")
    page.fill("#w-location", "Virtual Office")
    page.fill("#w-desc", "Verifying the new substantial card layout.")
    
    page.click("#save-work-entry")
    
    # Modal should close
    expect(page.locator("#work-modal")).not_to_be_visible()

    # 5. Verify the new card is substantial (desktop view)
    new_card = page.locator(".work-list-item:has-text('E2E Test Corp')")
    expect(new_card).to_be_visible()
    
    # Check for larger desktop styling (H5 for role instead of H6)
    role_header = new_card.locator("h5")
    expect(role_header).to_have_text("Desktop UI Tester")
    
    # Verify the card has a shadow and white background
    expect(new_card).to_have_class(re.compile(r"bg-white"))
    expect(new_card).to_have_class(re.compile(r"shadow-sm"))

    print("Admin Profile E2E Test Passed: Large desktop cards verified.")
