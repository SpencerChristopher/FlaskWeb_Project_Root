import os
import pathlib
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": True}


@pytest.mark.e2e
@pytest.mark.a11y
def test_homepage_accessibility(page: Page):
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:5000")
    axe_path = pathlib.Path("tests/axe/axe.min.js")

    if not axe_path.exists():
        pytest.skip(
            "Missing tests/axe/axe.min.js; run 'curl -L -o tests/axe/axe.min.js https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js' to enable."
        )

    page.goto(base_url, wait_until="domcontentloaded")

    # Handle Cookie Consent
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    # Load Axe from CDN (already allowed by CSP)
    page.add_script_tag(
        url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"
    )

    results = page.evaluate(
        """
        async () => {
            return await axe.run();
        }
    """
    )

    violations = results.get("violations", [])
    assert not violations, f"Accessibility violations found: {violations[:3]}"
