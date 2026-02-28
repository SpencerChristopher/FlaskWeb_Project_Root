import pytest

def test_contact_api_csrf_exemption(client):
    """
    Security Audit: Verify if the contact API is public (exempt from CSRF)
    but still protected by rate limiting.
    """
    payload = {
        "name": "Spammer",
        "email": "spam@example.com",
        "message": "Bulk spam message"
    }
    
    # Attempt POST without CSRF token
    response = client.post("/api/contact", json=payload)
    
    # We expect 200 OK because it's a public form, 
    # but we want to confirm it's intentional.
    assert response.status_code == 200
    assert response.get_json()["message"] == "Message sent successfully!"

def test_contact_api_throttling(client):
    """
    Security Audit: Verify the contact API enforces rate limits to prevent abuse.
    """
    payload = {"name": "A", "email": "a@b.com", "message": "msg"}
    
    # Hit the limit (configured at 5 per minute in code)
    for _ in range(5):
        client.post("/api/contact", json=payload)
        
    # The 6th request should be throttled
    response = client.post("/api/contact", json=payload)
    assert response.status_code == 429
