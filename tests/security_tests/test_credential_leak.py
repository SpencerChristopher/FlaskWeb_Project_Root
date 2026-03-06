import pytest
import logging
from src.models.user import User

def test_register_weak_password_rejected_and_not_logged(client, admin_headers, caplog):
    """
    Gating Test: Verifies that a weak password is REJECTED by the API and NOT
    found in the server's warning or error logs.
    """
    caplog.set_level(logging.WARNING)
    
    payload = {
        "username": "weak_user_gate",
        "email": "gate@test.com",
        "password": "tiny" # Unique weak password
    }
    
    response = client.post("/api/auth/register", json=payload, headers=admin_headers)
    
    # 1. Verification of Rejection (The 'Bypass' check)
    assert response.status_code == 400, f"Weak password should have been rejected with 400, got {response.status_code}"
    
    # 2. Verification of Redaction (The 'Leak' check)
    assert "tiny" not in caplog.text, "Sensitive password found in server logs"

def test_pydantic_error_details_no_echo(client, admin_headers):
    """
    Gating Test: Verifies that Pydantic validation errors do not echo the input
    back to the client in the 'details' field.
    """
    # Trigger a validation error on email format
    payload = {
        "username": "invalid_email_user",
        "email": "not-an-email",
        "password": "StrongPassword123!"
    }
    
    response = client.post("/api/auth/register", json=payload, headers=admin_headers)
    assert response.status_code == 400
    
    data = response.get_json()
    details_str = str(data.get("details", ""))
    
    # CURRENT BEHAVIOR: 'not-an-email' is often in the details via 'input' field
    assert "not-an-email" not in details_str, f"Input value echoed in error details: {details_str}"
