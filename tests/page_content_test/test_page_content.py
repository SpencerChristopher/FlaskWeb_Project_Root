import pytest

def test_base_html_serves_correctly(client):
    """
    Tests that the root URL (/) serves the base.html file, which is the SPA entry point.
    """
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode('utf-8')

    # Check for key structural elements from base.html by looking for stable IDs or attributes
    assert 'id="page-top"' in html
    assert 'id="mainNav"' in html
    assert '<header class="masthead">' in html
    assert 'id="home-content"' in html
    assert 'id="about-content"' in html
    assert 'src="/static/app.js"' in html

def test_navigation_links_are_present_in_base_html(client):
    """
    Tests that the main navigation links are present in the base HTML shell.
    This confirms the user has the ability to navigate.
    """
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode('utf-8')

    # Check for the navigation links that the SPA router depends on
    assert 'href="#home"' in html
    assert 'href="#about"' in html
    assert 'href="#blog"' in html
    assert 'href="#contact"' in html
    assert 'href="#license"' in html
