import pytest
from tests.security_tests.conftest import admin_headers, user_headers, admin_user, regular_user

@pytest.mark.usefixtures("clean_collections_per_function")
def test_get_profile_default(client):
    """Public can view the default profile even if none exists in DB."""
    resp = client.get("/api/content/profile")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Developer Name"
    assert data["skills"] == []
    assert data["work_history"] == []

@pytest.mark.usefixtures("clean_collections_per_function")
def test_admin_update_profile_complete(client, admin_headers):
    """Admin can update the profile with all fields."""
    update_data = {
        "name": "Chris Developer",
        "location": "London, UK",
        "statement": "Experienced Senior Developer specializing in Flask and Pi.",
        "interests": ["IoT", "Security"],
        "skills": ["Python", "Docker"],
        "social_links": {
            "github": "https://github.com/chris",
            "linkedin": "https://linkedin.com/in/chris"
        },
        "work_history": [
            {
                "company": "Tech Corp",
                "role": "Senior Engineer",
                "start_date": "2020-01",
                "end_date": "2023-01",
                "location": "Remote",
                "description": "Led backend team.",
                "skills": ["Python", "K8s"]
            }
        ]
    }
    resp = client.put("/api/content/profile", json=update_data, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Chris Developer"
    assert data["work_history"][0]["company"] == "Tech Corp"
    assert data["interests"] == ["IoT", "Security"]

@pytest.mark.usefixtures("clean_collections_per_function")
def test_member_cannot_update_profile(client, user_headers):
    """Members are forbidden from updating the profile."""
    update_data = {
        "name": "Hacker",
        "location": "Dark Web",
        "statement": "I have compromised your site.",
        "interests": [],
        "skills": [],
        "social_links": {},
        "work_history": []
    }
    resp = client.put("/api/content/profile", json=update_data, headers=user_headers)
    assert resp.status_code == 403


@pytest.mark.usefixtures("clean_collections_per_function")
def test_profile_rejects_external_image_url(client, admin_headers):
    update_data = {
        "name": "Chris Developer",
        "location": "London, UK",
        "statement": "Experienced Senior Developer specializing in Flask and Pi.",
        "interests": [],
        "skills": ["Python"],
        "social_links": {},
        "work_history": [],
        "image_url": "https://evil.example.com/image.png"
    }
    resp = client.put("/api/content/profile", json=update_data, headers=admin_headers)
    assert resp.status_code == 400
