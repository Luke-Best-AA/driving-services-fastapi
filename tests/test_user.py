import pytest
from app.user import User
from pydantic import ValidationError

def valid_user_dict():
    return {
        "user_id": 1,
        "username": "Alice1",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "alice@example.com",
        "is_admin": True
    }

def test_user_valid():
    user = User(**valid_user_dict())
    assert user.validate_user_values() is True

def test_user_invalid_username():
    data = valid_user_dict()
    data["username"] = "12345"  # Doesn't start with a letter
    user = User(**data)
    with pytest.raises(ValueError) as exc:
        user.validate_user_values()
    assert "username must be alphanumeric" in str(exc.value)

def test_user_short_username():
    data = valid_user_dict()
    data["username"] = "Al1"  # Too short
    user = User(**data)
    with pytest.raises(ValueError) as exc:
        user.validate_user_values()
    assert "at least 4 characters" in str(exc.value)

def test_user_invalid_password():
    data = valid_user_dict()
    data["password"] = "nothex"
    user = User(**data)
    with pytest.raises(ValueError) as exc:
        user.validate_user_values()
    assert "password must be a 32-character hexadecimal string" in str(exc.value)

def test_user_empty_password():
    data = valid_user_dict()
    data["password"] = ""
    user = User(**data)
    # Should not raise, empty password is allowed
    assert user.validate_user_values() is True

def test_user_invalid_email():
    data = valid_user_dict()
    data["email"] = "notanemail"
    user = User(**data)
    with pytest.raises(ValueError) as exc:
        user.validate_user_values()
    assert "email must be in format: name@example.com" in str(exc.value)

def test_user_invalid_is_admin():
    data = valid_user_dict()
    data["is_admin"] = 123
    with pytest.raises(ValidationError):
        User(**data)

def test_user_is_admin_int_true():
    data = valid_user_dict()
    data["is_admin"] = 1
    user = User(**data)
    assert user.validate_user_values() is True
    assert user.is_admin is True

def test_user_is_admin_int_false():
    data = valid_user_dict()
    data["is_admin"] = 0
    user = User(**data)
    assert user.validate_user_values() is True
    assert user.is_admin is False