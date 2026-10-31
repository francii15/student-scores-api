import pytest
from pydantic import ValidationError

from config import AppSettings


def valid_settings():
    return {
        "api_key": "test-only-key",
        "jwt_secret": (
            "test-only-jwt-secret-at-least-32-characters"
        ),
        "access_token_minutes": "30",
        "refresh_token_days": "7",
    }


def test_valid_settings():
    settings = AppSettings(**valid_settings())

    assert settings.access_token_minutes == 30
    assert settings.refresh_token_days == 7


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("api_key", ""),
        ("jwt_secret", ""),
        ("jwt_secret", "too-short"),
        ("access_token_minutes", 0),
        ("access_token_minutes", "not-a-number"),
        ("refresh_token_days", 31),
    ],
)
def test_invalid_settings(field, invalid_value):
    values = valid_settings()
    values[field] = invalid_value

    with pytest.raises(ValidationError) as error:
        AppSettings(**values)

    # Confirm the error identifies the invalid field.
    assert any(
        item["loc"] == (field,)
        for item in error.value.errors()
    )