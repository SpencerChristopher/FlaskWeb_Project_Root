import pytest
from pydantic import ValidationError
from src.schemas import ProfileSchema


def test_profile_schema_valid():
    """Verify that a valid profile data set passes validation."""
    data = {
        "name": "Chris Developer",
        "location": "United Kingdom",
        "statement": "Senior developer with 10 years experience.",
        "skills": ["Python", "Flask", "MongoDB"],
        "social_links": {
            "github": "https://github.com/testuser",
            "linkedin": "https://linkedin.com/in/testuser",
        },
    }
    schema = ProfileSchema(**data)
    assert schema.statement == data["statement"]
    assert len(schema.skills) == 3
    assert schema.social_links["github"] == "https://github.com/testuser"


def test_profile_schema_invalid_statement_length():
    """Verify that too short statements fail."""
    with pytest.raises(ValidationError):
        ProfileSchema(
            name="Chris", location="UK", statement="Short", skills=[], social_links={}
        )


def test_profile_schema_invalid_url():
    """Verify that non-absolute URLs in social_links fail."""
    data = {
        "name": "Chris",
        "location": "UK",
        "statement": "Senior developer with 10 years experience.",
        "social_links": {"github": "not-a-url"},
    }
    with pytest.raises(ValidationError) as excinfo:
        ProfileSchema(**data)
    assert "URL must be absolute" in str(excinfo.value)
