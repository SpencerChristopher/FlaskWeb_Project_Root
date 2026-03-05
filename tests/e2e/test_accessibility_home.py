import os
import pathlib
import pytest

playwright = pytest.importorskip("playwright.sync_api")
Page = playwright.Page


@pytest.mark.e2e
@pytest.mark.a11y
def test_homepage_accessibility(page: Page):
    base_url = os.getenv("E2E_BASE_URL")
    axe_path = pathlib.Path("tests/axe/axe.min.js")

    if not base_url:
        pytest.skip("Set E2E_BASE_URL to enable Playwright a11y checks.")
    if not axe_path.exists():
        pytest.skip("Missing tests/axe/axe.min.js; add axe core script to enable a11y checks.")

    page.goto(base_url, wait_until="domcontentloaded")
    page.add_script_tag(path=str(axe_path))
    results = page.evaluate("""
        async () => {
            return await axe.run();
        }
    """)

    violations = results.get("violations", [])
    assert not violations, f"Accessibility violations found: {violations[:3]}"
