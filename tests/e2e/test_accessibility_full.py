import pathlib
import pytest
from playwright.sync_api import Page, expect, Browser

ROUTES = [
    "/",
    "/blog",
    "/about",
    "/contact",
    "/login",
    "/license",
    "/privacy",
]

@pytest.fixture(scope="function")
def context(browser: Browser):
    context = browser.new_context(bypass_csp=True)
    yield context
    context.close()

@pytest.fixture(scope="function")
def page(context):
    page = context.new_page()
    yield page
    page.close()

@pytest.mark.e2e
@pytest.mark.a11y
@pytest.mark.parametrize("path", ROUTES)
def test_accessibility(page: Page, base_url: str, path: str):
    axe_path = pathlib.Path("tests/axe/axe.min.js")

    if not axe_path.exists():
        pytest.skip("Missing tests/axe/axe.min.js")

    page.goto(f"{base_url}{path}", wait_until="domcontentloaded")

    # Handle Cookie Consent if visible
    accept_btn = page.locator("[data-test='cookie-accept']")
    if accept_btn.is_visible():
        accept_btn.click()

    # Wait for SPA content to load
    if path == "/":
        page.wait_for_selector("[data-test='view-home']")
    elif path == "/blog":
        page.wait_for_selector("[data-test='article-grid']")
    elif path == "/contact":
        page.wait_for_selector("#contactForm")
    elif path == "/login":
        page.wait_for_selector("#loginForm")
    
    # Inject local Axe
    page.add_script_tag(path=str(axe_path))

    results = page.evaluate(
        """
        async () => {
            return await axe.run();
        }
    """
    )

    violations = results.get("violations", [])
    if violations:
        print(f"\n--- Accessibility Violations on {path} ---")
        for v in violations:
            print(f"Violation: {v['id']} ({v['impact']})")
            print(f"Description: {v['description']}")
            print(f"Help: {v['help']} ({v['helpUrl']})")
            for node in v['nodes']:
                print(f"  - Target: {node['target']}")
                print(f"    Snippet: {node['html']}")
        print("-------------------------------------------\n")
    
    assert not violations, f"Accessibility violations found on {path}: {[v['id'] for v in violations]}"
