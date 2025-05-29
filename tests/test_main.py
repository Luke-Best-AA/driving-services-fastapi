from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app, verify_token
from app.user import User
from app.messages import Messages
from app.response import APIResponse

import datetime
import pytest
import jwt
from dotenv import load_dotenv
import os
import importlib
from http import HTTPStatus
import math

# Load environment variables from .env file
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")  # Load SECRET_KEY from .env
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in the environment variables")

ALGORITHM = "HS256"  # JWT signing algorithm

client = TestClient(app)

class TokenData:
    """Helper class to generate tokens for testing."""
    @staticmethod
    def create_token(user_id: int, expires_in: datetime.timedelta):
        token_data = {
            "user_id": user_id,
            "exp": datetime.datetime.now(datetime.timezone.utc) + expires_in
        }
        return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_expired_token(user_id: int):
        token_data = {
            "user_id": user_id,
            "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)
        }
        return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
def get_policy_dates():
    # Set start date to 30 days in the future
    start_date = datetime.date.today() + datetime.timedelta(days=30)
    # Set end date to 1 year minus 1 day after start date
    end_date = start_date + datetime.timedelta(days=365 - 1)
    # Convert to string in YYYY-MM-DD format
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    return start_date_str, end_date_str    
    
@pytest.fixture
def admin_token():
    """Fixture to create a valid admin token."""
    return TokenData.create_token(user_id=1, expires_in=datetime.timedelta(minutes=15))

@pytest.fixture
def non_admin_token():
    """Fixture to create a valid non-admin token."""
    return TokenData.create_token(user_id=2, expires_in=datetime.timedelta(minutes=15))
    
@pytest.fixture
def valid_admin_user():
    class UserMock:
        user_id = 1
        username = "admin"
        email = "admin@email.com"
        is_admin = True
    return UserMock()

@pytest.fixture
def valid_non_admin_user():
    class UserMock:
        user_id = 2
        username = "nonadmin"
        email = "nonadmin@email.com"
        is_admin = False
    return UserMock()

@pytest.fixture
def valid_admin_data():
    return {"username": "admin", "password": "adminpass"}

@pytest.fixture
def valid_non_admin_data():
    return {"username": "nonadmin", "password": "userpass"}

@pytest.fixture
def invalid_user_data():
    return {"username": "invalid", "password": "wrong"}    

@pytest.fixture
def mock_cursor(mocker):
    """Fixture to mock the database cursor."""
    return mocker.Mock()

@pytest.fixture
def admin_user():
    """Fixture to create an admin user."""
    return User(user_id=1, username="admin", password="password", email="test@email.com", is_admin=True)

@pytest.fixture
def non_admin_user():
    """Fixture to create a non-admin user."""
    return User(user_id=2, username="nonadmin", password="password", email="test@email.com", is_admin=False)

@pytest.fixture
def valid_optional_extra_data():
    return {
        "extra_id": 1,
        "name": "Updated Extra",
        "code": "UPDATED_EXTRA",
        "price": 15.0
    }

@pytest.fixture
def mock_policy():
    return {
        "ci_policy_id": 1,
        "user_id": 1,
        "vrn": "ABC123",
        "make": "Toyota",
        "model": "Corolla",
        "policy_number": "POL12345",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "coverage": "Comprehensive"
    }

@pytest.fixture
def mock_policies(mock_policy):
    return [mock_policy]

@pytest.fixture
def mock_policies_with_extras(mock_policy):
    return [{
        "policy": mock_policy,
        "optional_extras": [
            {"extra_id": 1, "name": "Roadside Assistance", "code": "RA001", "price": 50.0}
        ]
    }]

def patch_user_and_service(mocker, user, policies, policies_with_extras):
    mocker.patch("app.services.user_service.UserService.get_user_by_id", return_value=user)
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.list_all_car_insurance_policies", return_value=policies)
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.get_car_insurance_policy_by_id", return_value=policies)
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.get_car_insurance_policy_by_user_id", return_value=policies)
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.filter_car_insurance_policies", return_value=policies)
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.get_policy_extras", return_value=policies_with_extras)
    mocker.patch("app.main.verify_token", return_value={"user_id": user.user_id})

def mock_authenticate_user_success(user):
    async def _mock(self, username, password):
        return user
    return _mock

def mock_authenticate_user_fail(self, username, password):
    raise ValueError("Invalid credentials")

def test_no_authorization_header():
    response = client.get("/read_user")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": Messages.AUTHORIZATION_HEADER_MISSING}

def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": Messages.API_IS_RUNNNG}

def test_token_admin(mocker, valid_admin_data, valid_admin_user):
    mocker.patch("app.services.user_service.UserService.authenticate_user", mock_authenticate_user_success(valid_admin_user))
    response = client.post("/token", data=valid_admin_data)
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["user"]["username"] == "admin"
    assert data["user"]["is_admin"] is True
    assert "access_token" in data

def test_token_non_admin(mocker, valid_non_admin_data, valid_non_admin_user):
    mocker.patch("app.services.user_service.UserService.authenticate_user", mock_authenticate_user_success(valid_non_admin_user))
    response = client.post("/token", data=valid_non_admin_data)
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["user"]["username"] == "nonadmin"
    assert data["user"]["is_admin"] is False
    assert "access_token" in data

def test_token_invalid(mocker, invalid_user_data):
    mocker.patch("app.services.user_service.UserService.authenticate_user", side_effect=ValueError("Invalid credentials"))
    response = client.post("/token", data=invalid_user_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "access_token" not in response.json()

def test_refresh_token_valid():
    # Create a valid refresh token
    refresh_token = TokenData.create_token(user_id=1, expires_in=datetime.timedelta(days=7))

    # Send the refresh token to the endpoint
    response = client.post("/refresh_token", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200

    # Verify the response contains new tokens
    response_data = response.json()
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert response_data["token_type"] == "bearer"

def test_refresh_token_expired():
    # Create an expired refresh token
    expired_refresh_token = TokenData.create_expired_token(user_id=1)

    # Send the expired refresh token to the endpoint
    response = client.post("/refresh_token", headers={"Authorization": f"Bearer {expired_refresh_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": Messages.REFRESH_TOKEN_EXPIRED}

def test_refresh_token_invalid():
    # Create an invalid refresh token
    invalid_refresh_token = "invalid.token.value"

    # Send the invalid refresh token to the endpoint
    response = client.post("/refresh_token", headers={"Authorization": f"Bearer {invalid_refresh_token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": Messages.INVALID_REFRESH_TOKEN}

def test_verify_token_valid():
    # Create a valid token
    valid_token = TokenData.create_token(user_id=1, expires_in=datetime.timedelta(minutes=15))

    # Call the verify_token function
    decoded_token = verify_token(valid_token)
    assert decoded_token["user_id"] == 1

def test_verify_token_expired():
    # Create an expired token
    expired_token = TokenData.create_expired_token(user_id=1)

    # Call the verify_token function and expect an HTTPException
    with pytest.raises(HTTPException) as exc_info:
        verify_token(expired_token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == Messages.TOKEN_HAS_EXPIRED

def test_verify_token_invalid():
    # Create an invalid token
    invalid_token = "invalid.token.value"

    # Call the verify_token function and expect an HTTPException
    with pytest.raises(HTTPException) as exc_info:
        verify_token(invalid_token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == Messages.INVALID_TOKEN

def test_create_user_valid(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)

    # Mock the database insert operation
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", return_value=3)  # Simulate user_id 3 being created

    # Send a request to create a new user
    new_user_data = {
        "user_id" : 0,
        "username": "newuser",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "newuser@example.com",
        "is_admin": False
    }
    response = client.post("/create_user", json=new_user_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.CREATED
    response_data = response.json()
    assert response_data["message"] == Messages.USER_CREATED_SUCCESS
    assert response_data["user"]["username"] == "newuser"
    assert response_data["user"]["email"] == "newuser@example.com"
    assert response_data["user"]["is_admin"] is False

def test_create_user_invalid(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # validation error
    new_user_data = {
        "user_id" : 0,
        "username": "newuser",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "invalidemail",
        "is_admin": False
    }
    response = client.post("/create_user", json=new_user_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_create_user_non_admin(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)

    # Send a request to create a new user
    new_user_data = {
        "user_id" : 0,
        "username": "newuser",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "newuser@email.com",
        "is_admin": False
    }
    response = client.post("/create_user", json=new_user_data, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION}

def test_create_user_duplicate(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)

    # Mock the database insert operation to raise a unique constraint error
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", side_effect=ValueError(APIResponse(status=HTTPStatus.CONFLICT, message=Messages.DUPLICATION_ERROR, data=None)))

    # Send a request to create a new user
    new_user_data = {
        "user_id" : 0,
        "username": "existinguser",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "existinguser@example.com",
        "is_admin": False
    }
    response = client.post("/create_user", json=new_user_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {"detail": Messages.DUPLICATION_ERROR}

# test that httpexception is raised if httpexception during database operation (error code 500)
def test_create_user_database_error(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)

    # Mock the database insert operation to raise a generic database error
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", side_effect=ValueError(APIResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR, message=Messages.DB_ERROR, data=None)))

    # Send a request to create a new user
    new_user_data = {
        "user_id": 0,
        "username": "newuser",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "newuser@example.com",
        "is_admin": False
    }
    response = client.post("/create_user", json=new_user_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": Messages.DB_ERROR}

def test_read_user_list_all_admin(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)

    # Mock the database query for listing all users
    mocker.patch("app.statements.SelectStatementExecutor.execute_select", return_value=[
        {"user_id": 1, "username": "admin", "email": "admin@example.com", "is_admin": True},
        {"user_id": 2, "username": "user", "email": "user@example.com", "is_admin": False}
    ])

    # Send a request to list all users
    response = client.get("/read_user", params={"mode": "list_all"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == Messages.USER_READ_SUCCESS
    users = response_data["users"]
    assert len(users) == 2
    assert users[0]["username"] == "admin"
    assert users[1]["username"] == "user"

def test_read_user_list_all_non_admin(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Send a request to list all users
    response = client.get("/read_user", params={"mode": "list_all"}, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION}

def test_read_user_filter_admin(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    mocker.patch("app.services.user_service.UserService.check_admin", return_value=True)

    # Mock the database query for filtering users
    mocker.patch("app.statements.SelectStatementExecutor.execute_select", return_value=[
        {"user_id": 2, "username": "user", "email": "user@example.com", "is_admin": False}
    ])

    # Send a request to filter users by username
    response = client.get("/read_user", params={"mode": "filter", "field": "username", "value": "user"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == Messages.USER_READ_SUCCESS
    users = response_data["users"]
    assert len(users) == 1
    assert users[0]["username"] == "user"

def test_read_user_filter_non_admin(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Send a request to filter users
    response = client.get("/read_user", params={"mode": "filter", "field": "username", "value": "user"}, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION}

def test_read_user_by_id_admin(admin_token, mocker, valid_admin_user):
    # Admin can get Id not equal to their own
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)

    # Mock the database query for retrieving a user by ID
    mocker.patch("app.statements.SelectStatementExecutor.execute_select", return_value=[
        {"user_id": 2, "username": "user", "email": "user@example.com", "is_admin": False}
    ])

    # Send a request to retrieve a user by ID
    response = client.get("/read_user", params={"mode": "by_id", "user_id": 2}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == Messages.USER_READ_SUCCESS
    users = response_data["users"]
    assert len(users) == 1
    assert users[0]["username"] == "user"

def test_read_user_by_id_non_admin(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Mock the database query for retrieving a user by ID
    mocker.patch("app.statements.SelectStatementExecutor.execute_select", return_value=[
        {"user_id": 2, "username": "user", "email": "user@example.com", "is_admin": False}
    ])

    # Send a request to retrieve a user by ID
    response = client.get("/read_user", params={"mode": "by_id", "user_id": 2}, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == Messages.USER_READ_SUCCESS
    users = response_data["users"]
    assert len(users) == 1
    assert users[0]["username"] == "user"

def test_read_user_by_id_non_admin_forbidden(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Mock the database query for retrieving a user by ID
    mocker.patch("app.statements.SelectStatementExecutor.execute_select", return_value=[
        {"user_id": 2, "username": "user", "email": "user@example.com", "is_admin": False}
    ])

    # Send a request to retrieve a user by ID where the user_id does not match the non-admin's user_id
    response = client.get("/read_user", params={"mode": "by_id", "user_id": 3}, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION}

def test_read_user_myself(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)

    # Mock the database query for retrieving the user's own details
    mocker.patch("app.statements.SelectStatementExecutor.execute_select", return_value=[
        {"user_id": 2, "username": "user", "email": "user@example.com", "is_admin": False}
    ])

    # Send a request to retrieve the user's own details
    response = client.get("/read_user", params={"mode": "myself"}, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == Messages.USER_READ_SUCCESS
    users = response_data["users"]
    assert len(users) == 1
    assert users[0]["username"] == "user"

def test_read_user_invalid_mode(admin_token):
    # Send a request with an invalid mode
    response = client.get("/read_user", params={"mode": "invalid_mode"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": Messages.USER_INVALID_READ_MODE}

def test_read_user_filter_missing_field(admin_token):
    # Send a request to filter users without providing the field parameter
    response = client.get("/read_user", params={"mode": "filter", "value": "user"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": Messages.FIELD_REQUIRED.format("field")}

def test_read_user_filter_missing_value(admin_token):
    # Send a request to filter users without providing the value parameter
    response = client.get("/read_user", params={"mode": "filter", "field": "username"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": Messages.FIELD_REQUIRED.format("value")}

def test_read_user_filter_missing_field_and_value(admin_token):
    # Send a request to filter users without providing both field and value parameters
    response = client.get("/read_user", params={"mode": "filter"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": Messages.FIELD_REQUIRED.format("field")}

def test_read_user_by_id_missing_user_id(admin_token):
    # Send a request to retrieve a user by ID without providing the user_id parameter
    response = client.get("/read_user", params={"mode": "by_id"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": Messages.FIELD_REQUIRED.format("user_id")}

def test_update_user_valid_admin(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)

    # Mock the database update operation
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", return_value=None)

    # Send a request to update a user
    updated_user_data = {
        "user_id": 3,
        "username": "updateduser",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "updateduser@example.com",
        "is_admin": False
    }
    response = client.put("/update_user", params={"user_id": 3}, json=updated_user_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == Messages.USER_UPDATED_SUCCESS
    user = response_data["user"]
    assert user["username"] == "updateduser"

def test_update_user_valid_non_admin(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Mock the database update operation
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", return_value=None)
    # Send a request to update the user's own details
    updated_user_data = {
        "user_id": 2,
        "username": "updateduser",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "updateduser@example.com",
        "is_admin": False
    }
    response = client.put("/update_user", params={"user_id": 2}, json=updated_user_data, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == Messages.USER_UPDATED_SUCCESS
    user = response_data["user"]
    assert user["username"] == "updateduser"

def test_update_user_valid_non_admin_forbidden(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Mock the database update operation
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", return_value=None)
    # Send a request to update another user's details
    updated_user_data = {
        "user_id": 3,
        "username": "updateduser",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "updateduser@example.com",
        "is_admin": False
    }
    response = client.put("/update_user", params={"user_id": 3}, json=updated_user_data, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION_CHANGE}

def test_update_user_invalid_id(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database update operation to raise an exception
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", side_effect=ValueError(APIResponse(status=HTTPStatus.NOT_FOUND, message=Messages.USER_NOT_FOUND, data=None)))
    # Send a request to update a user with an invalid ID
    updated_user_data = {
        "user_id": 999,
        "username": "updateduser",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "updateduser@example.com",
        "is_admin": False
    }
    response = client.put("/update_user", params={"user_id": 999}, json=updated_user_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": Messages.USER_NOT_FOUND}
def test_update_user_invalid_data(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database update operation
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", return_value=None)
    # Send a request to update a user with invalid data
    updated_user_data = {
        "user_id": 3,
        "username": "updateduser",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "invalidemail",
        "is_admin": False
    }
    response = client.put("/update_user", params={"user_id": 3}, json=updated_user_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_update_user_database_error(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)

    # Mock the database update operation to raise an exception
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", side_effect=ValueError(APIResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR, message=Messages.DB_ERROR, data=None)))

    # Send a request to update a user
    updated_user_data = {
        "user_id": 3,
        "username": "updateduser",
        "password": "5f4dcc3b5aa765d61d8327deb882cf99",
        "email": "updateduser@example.com",
        "is_admin": False
    }
    response = client.put("/update_user", params={"user_id": 3}, json=updated_user_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": Messages.DB_ERROR}

def test_delete_user_valid_admin(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)

    # Mock the database delete operation
    mocker.patch("app.statements.DeleteStatementExecutor.execute_delete", return_value=None)

    # Send a request to delete a user
    response = client.delete("/delete_user", params={"user_id": 3}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == Messages.USER_DELETED_SUCCESS
    assert response_data["user_id"] == 3

def test_delete_user_valid_non_admin(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Mock the database delete operation
    mocker.patch("app.statements.DeleteStatementExecutor.execute_delete", return_value=None)
    # Send a request to delete the user's own account
    response = client.delete("/delete_user", params={"user_id": 2}, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION}

def test_delete_user_database_error(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)

    # Mock the database delete operation to raise an exception
    mocker.patch("app.statements.DeleteStatementExecutor.execute_delete", side_effect=ValueError(APIResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR, message=Messages.DB_ERROR, data=None)))

    # Send a request to delete a user
    response = client.delete("/delete_user", params={"user_id": 3}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": Messages.DB_ERROR}

def test_delete_user_invalid_id(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database delete operation to raise an exception
    mocker.patch("app.statements.DeleteStatementExecutor.execute_delete", side_effect=ValueError(APIResponse(status=HTTPStatus.NOT_FOUND, message=Messages.USER_NOT_FOUND, data=None)))
    # Send a request to delete a user with an invalid ID
    response = client.delete("/delete_user", params={"user_id": 999}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": Messages.USER_NOT_FOUND}

def test_create_optional_extra_valid_admin(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)

    # Mock the database insert operation
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", return_value=3)  # Simulate optional_extra_id 3 being created

    # Send a request to create a new optional extra
    new_optional_extra_data = {
        "extra_id": 0,
        "name": "Extra1",
        "code": "EXTRA1",
        "price": 10.0
    }
    response = client.post("/create_optional_extra", json=new_optional_extra_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.CREATED
    response_data = response.json()
    assert response_data["message"] == "Optional extra created successfully"
    assert response_data["optional_extra"]["name"] == "Extra1"
    assert response_data["optional_extra"]["code"] == "EXTRA1"
    assert math.isclose(response_data["optional_extra"]["price"], 10.0, rel_tol=1e-9)

def test_create_optional_extra_valid_non_admin(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Mock the database insert operation
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", return_value=3)  # Simulate optional_extra_id 3 being created
    # Send a request to create a new optional extra
    new_optional_extra_data = {
        "extra_id": 0,
        "name": "Extra1",
        "code": "EXTRA1",
        "price": 10.0
    }
    response = client.post("/create_optional_extra", json=new_optional_extra_data, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION}

def test_create_optional_extra_invalid_data(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database insert operation
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", return_value=3)  # Simulate optional_extra_id 3 being created
    # Send a request to create a new optional extra with invalid data
    new_optional_extra_data = {
        "extra_id": 0,
        "name": "Extra1",
        "code": "EXTRA1",
        "price": "invalid_price"  # Invalid price
    }
    response = client.post("/create_optional_extra", json=new_optional_extra_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_create_optional_extra_duplicate(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database insert operation to raise a unique constraint error
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", side_effect=ValueError(APIResponse(status=HTTPStatus.CONFLICT, message=Messages.DUPLICATION_ERROR, data=None)))
    # Send a request to create a new optional extra
    new_optional_extra_data = {
        "extra_id": 0,
        "name": "Extra1",
        "code": "EXTRA1",
        "price": 10.0
    }
    response = client.post("/create_optional_extra", json=new_optional_extra_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {"detail": Messages.DUPLICATION_ERROR}

def test_create_optional_extra_database_error(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database insert operation to raise a generic database error
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", side_effect=ValueError(APIResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR, message=Messages.DB_ERROR, data=None)))
    # Send a request to create a new optional extra
    new_optional_extra_data = {
        "extra_id": 0,
        "name": "Extra1",
        "code": "EXTRA1",
        "price": 10.0
    }
    response = client.post("/create_optional_extra", json=new_optional_extra_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": Messages.DB_ERROR}

def test_read_optional_extra_list_all(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)

    # Mock the database query for listing all optional extras
    mocker.patch("app.statements.SelectStatementExecutor.execute_select", return_value=[
        {"extra_id": 1, "name": "Extra1", "code": "EXTRA1", "price": 10.0},
        {"extra_id": 2, "name": "Extra2", "code": "EXTRA2", "price": 20.0}
    ])

    # Send a request to list all optional extras
    response = client.get("/read_optional_extra", params={"mode": "list_all"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == Messages.OPTIONAL_EXTRA_READ_SUCCESS
    optional_extras = response_data["optional_extras"]
    assert len(optional_extras) == 2
    assert optional_extras[0]["name"] == "Extra1"
    assert optional_extras[1]["name"] == "Extra2"

def test_read_optional_extra_by_id(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database query for retrieving an optional extra by ID
    mocker.patch("app.statements.SelectStatementExecutor.execute_select", return_value=[
        {"extra_id": 1, "name": "Extra1", "code": "EXTRA1", "price": 10.0}
    ])
    # Send a request to retrieve an optional extra by ID
    response = client.get("/read_optional_extra", params={"mode": "by_id", "extra_id": 1}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == Messages.OPTIONAL_EXTRA_READ_SUCCESS
    optional_extra = response_data["optional_extras"][0]
    assert optional_extra["name"] == "Extra1"
    assert optional_extra["code"] == "EXTRA1"
    assert math.isclose(optional_extra["price"], 10.0, rel_tol=1e-9)

def test_read_optional_extra_invalid_mode(admin_token):
    # Send a request with an invalid mode
    response = client.get("/read_optional_extra", params={"mode": "invalid_mode"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": Messages.OPTIONAL_EXTRA_INVALID_READ_MODE}

def test_read_optional_extra_by_id_missing_extra_id(admin_token):
    # Send a request to retrieve an optional extra by ID without providing the extra_id parameter
    response = client.get("/read_optional_extra", params={"mode": "by_id"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": Messages.FIELD_REQUIRED.format("extra_id")}

def test_update_optional_extra_valid_admin(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database update operation
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", return_value=None)
    # Send a request to update an optional extra
    updated_optional_extra_data = {
        "extra_id": 1,
        "name": "Updated Extra",
        "code": "UEXTRA",
        "price": 15.0
    }
    response = client.put("/update_optional_extra", params={"extra_id": 1}, json=updated_optional_extra_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == "Optional extra updated successfully"
    optional_extra = response_data["optional_extra"]
    assert optional_extra["name"] == "Updated Extra"
    assert optional_extra["code"] == "UEXTRA"
    assert math.isclose(optional_extra["price"], 15.0, rel_tol=1e-9)

def test_update_optional_extra_valid_non_admin(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Mock the database update operation
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", return_value=None)
    # Send a request to update an optional extra
    updated_optional_extra_data = {
        "extra_id": 1,
        "name": "Updated Extra",
        "code": "UEXTRA",
        "price": 15.0
    }
    response = client.put("/update_optional_extra", params={"extra_id": 1}, json=updated_optional_extra_data, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION}

def test_update_optional_extra_invalid_data(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database update operation
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", return_value=None)
    # Send a request to update an optional extra with invalid data
    updated_optional_extra_data = {
        "extra_id": 1,
        "name": "Updated Extra",
        "code": "UEXTRA",
        "price": "invalid_price"  # Invalid price
    }
    response = client.put("/update_optional_extra", params={"extra_id": 1}, json=updated_optional_extra_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_update_optional_extra_invalid_id(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database update operation to raise an exception
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", side_effect=ValueError(APIResponse(status=HTTPStatus.NOT_FOUND, message=Messages.OPTIONAL_EXTRA_NOT_FOUND, data=None)))
    # Send a request to update an optional extra with an invalid ID
    updated_optional_extra_data = {
        "extra_id": 999,
        "name": "Updated Extra",
        "code": "UEXTRA",
        "price": 15.0
    }
    response = client.put("/update_optional_extra", params={"extra_id": 999}, json=updated_optional_extra_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": Messages.OPTIONAL_EXTRA_NOT_FOUND}

def test_update_optional_extra_database_error(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database update operation to raise an exception
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", side_effect=ValueError(APIResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR, message=Messages.DB_ERROR, data=None)))
    # Send a request to update an optional extra
    updated_optional_extra_data = {
        "extra_id": 1,
        "name": "Updated Extra",
        "code": "UEXTRA",
        "price": 15.0
    }
    response = client.put("/update_optional_extra", params={"extra_id": 1}, json=updated_optional_extra_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": Messages.DB_ERROR}

def test_update_optional_extra_missing_extra(admin_token):
    # Send a request to update an optional extra without providing the extra_id parameter
    response = client.put("/update_optional_extra", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_delete_optional_extra_valid_admin(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database delete operation
    mocker.patch("app.statements.DeleteStatementExecutor.execute_delete", return_value=None)
    # Send a request to delete an optional extra
    response = client.delete("/delete_optional_extra", params={"extra_id": 1}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert response_data["message"] == "Optional extra deleted successfully"
    assert response_data["extra_id"] == 1

def test_delete_optional_extra_valid_non_admin(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Mock the database delete operation
    mocker.patch("app.statements.DeleteStatementExecutor.execute_delete", return_value=None)
    # Send a request to delete an optional extra
    response = client.delete("/delete_optional_extra", params={"extra_id": 1}, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION}

def test_delete_optional_extra_invalid_id(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database delete operation to raise an exception
    mocker.patch("app.statements.DeleteStatementExecutor.execute_delete", side_effect=ValueError(APIResponse(status=HTTPStatus.NOT_FOUND, message=Messages.OPTIONAL_EXTRA_NOT_FOUND, data=None)))
    # Send a request to delete an optional extra with an invalid ID
    response = client.delete("/delete_optional_extra", params={"extra_id": 999}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": Messages.OPTIONAL_EXTRA_NOT_FOUND}

def test_delete_optional_extra_database_error(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database delete operation to raise an exception
    mocker.patch("app.statements.DeleteStatementExecutor.execute_delete", side_effect=ValueError(APIResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR, message=Messages.DB_ERROR, data=None)))
    # Send a request to delete an optional extra
    response = client.delete("/delete_optional_extra", params={"extra_id": 1}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": Messages.DB_ERROR}

def test_delete_optional_extra_missing_extra_id(admin_token):
    # Send a request to delete an optional extra without providing the extra_id parameter
    response = client.delete("/delete_optional_extra", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_create_car_insurance_policy_valid_admin(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database insert operation
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", return_value=101)  # Simulate policy ID 101 being created
    # Mock the database insert operation for optional extras
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert_many", return_value=None)
    # Send a request to create a car insurance policy
    policy_data = {
        "user_id": 1,
        "vrn": "ABC123",
        "make": "Toyota",
        "model": "Corolla",
        "policy_number": "POL12345",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "coverage": "Comprehensive"
    }
    optional_extras = [
        {"extra_id": 1, "name": "Roadside Assistance", "code": "RA001", "price": 50.0},
        {"extra_id": 3, "name": "Personal Accident Cover", "code": "PAC003", "price": 75.0}
    ]
    response = client.post(
        "/create_car_insurance_policy",
        json={"policy": policy_data, "optional_extras": optional_extras},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.CREATED
    response_data = response.json()
    assert response_data["message"] == Messages.POLICY_CREATED_SUCCESS
    assert response_data["policy"]["ci_policy_id"] == 101
    assert response_data["policy"]["policy_number"] == "POL12345"
    assert response_data["policy"]["user_id"] == 1
    assert response_data["policy"]["vrn"] == "ABC123"
    assert response_data["policy"]["make"] == "Toyota"
    assert response_data["policy"]["model"] == "Corolla"
    assert response_data["policy"]["start_date"] == "2025-01-01"
    assert response_data["policy"]["end_date"] == "2025-12-31"
    assert response_data["policy"]["coverage"] == "Comprehensive"
    assert response_data["optional_extras"] == [
        {"extra_id": 1, "name": "Roadside Assistance", "code": "RA001", "price": 50.0},
        {"extra_id": 3, "name": "Personal Accident Cover", "code": "PAC003", "price": 75.0}
    ]

def test_create_car_insurance_policy_valid_non_admin(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Mock the database insert operation
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", return_value=101)  # Simulate policy ID 101 being created
    # Mock the database insert operation for optional extras
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert_many", return_value=None)
    # Send a request to create a car insurance policy for their own user_id
    start_date, end_date = get_policy_dates()
    policy_data = {
        "ci_policy_id": 0,
        "user_id": 2,
        "vrn": "XYZ789",
        "make": "Honda",
        "model": "Civic",
        "policy_number": "POL67890",
        "start_date": start_date,
        "end_date": end_date,
        "coverage": "Third Party"
    }
    optional_extras = [
        {"extra_id": 1, "name": "Roadside Assistance", "code": "RA001", "price": 50.0},
        {"extra_id": 3, "name": "Personal Accident Cover", "code": "PAC003", "price": 75.0}
    ]
    print(f"Policy Data: {policy_data}")
    print(f"Optional Extras: {optional_extras}")
    response = client.post(
        "/create_car_insurance_policy",
        json={"policy": policy_data, "optional_extras": optional_extras},
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert response.status_code == HTTPStatus.CREATED
    response_data = response.json()
    assert response_data["message"] == Messages.POLICY_CREATED_SUCCESS
    assert response_data["policy"]["ci_policy_id"] == 101
    assert response_data["policy"]["policy_number"] == "POL67890"
    assert response_data["policy"]["user_id"] == 2
    assert response_data["policy"]["vrn"] == "XYZ789"
    assert response_data["policy"]["make"] == "Honda"
    assert response_data["policy"]["model"] == "Civic"
    assert response_data["policy"]["start_date"] == start_date
    assert response_data["policy"]["end_date"] == end_date
    assert response_data["policy"]["coverage"] == "Third Party"
    assert response_data["optional_extras"] == [
        {"extra_id": 1, "name": "Roadside Assistance", "code": "RA001", "price": 50.0},
        {"extra_id": 3, "name": "Personal Accident Cover", "code": "PAC003", "price": 75.0}
    ]

def test_create_car_insurance_policy_valid_non_admin_forbidden(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    # Mock the database insert operation
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", return_value=101)  # Simulate policy ID 101 being created
    # Mock the database insert operation for optional extras
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert_many", return_value=None)
    # Send a request to create a car insurance policy for another user
    start_date, end_date = get_policy_dates()
    policy_data = {
        "user_id": 1,  # Non-admin trying to create a policy for another user
        "vrn": "ABC123",
        "make": "Toyota",
        "model": "Corolla",
        "policy_number": "POL12345",
        "start_date": start_date,
        "end_date": end_date,
        "coverage": "Comprehensive"
    }
    optional_extras = [
        {"extra_id": 1, "name": "Roadside Assistance", "code": "RA001", "price": 50.0},
        {"extra_id": 3, "name": "Personal Accident Cover", "code": "PAC003", "price": 75.0}
    ]
    response = client.post(
        "/create_car_insurance_policy",
        json={"policy": policy_data, "optional_extras": optional_extras},
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION}

def test_create_car_insurance_policy_invalid_data(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database insert operation
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", return_value=101)  # Simulate policy ID 101 being created
    # Mock the database insert operation for optional extras
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert_many", return_value=None)
    # Send a request to create a car insurance policy with invalid data
    policy_data = {
        "user_id": 1,
        "vrn": "ABC123",
        "make": "Toyota",
        "model": "Corolla",
        "policy_number": "POL1 2345", # Invalid policy number format
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "coverage": "Comprehensive"
    }
    optional_extras = [
        {"extra_id": 1, "name": "Roadside Assistance", "code": "RA001", "price": 50.0},
        {"extra_id": 3, "name": "Personal Accident Cover", "code": "PAC003", "price": 75.0}
    ]
    response = client.post(
        "/create_car_insurance_policy",
        json={"policy": policy_data, "optional_extras": optional_extras},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_create_car_insurance_policy_duplicate(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database insert operation to raise a unique constraint error
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", side_effect=ValueError(APIResponse(status=HTTPStatus.CONFLICT, message=Messages.DUPLICATION_ERROR, data=None)))
    # Send a request to create a car insurance policy
    start_date, end_date = get_policy_dates()
    policy_data = {
        "user_id": 1,
        "vrn": "ABC123",
        "make": "Toyota",
        "model": "Corolla",
        "policy_number": "POL12345",
        "start_date": start_date,
        "end_date": end_date,
        "coverage": "Comprehensive"
    }
    optional_extras = [
        {"extra_id": 1, "name": "Roadside Assistance", "code": "RA001", "price": 50.0},
        {"extra_id": 3, "name": "Personal Accident Cover", "code": "PAC003", "price": 75.0}
    ]
    response = client.post(
        "/create_car_insurance_policy",
        json={"policy": policy_data, "optional_extras": optional_extras},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {"detail": Messages.DUPLICATION_ERROR}

def test_create_car_insurance_policy_invalid_optional_extras(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database insert operation
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", return_value=101)  # Simulate policy ID 101 being created
    # Mock the database insert operation for optional extras
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert_many", return_value=None)
    # Send a request to create a car insurance policy with invalid optional extras
    start_date, end_date = get_policy_dates()
    policy_data = {
        "user_id": 1,
        "vrn": "ABC123",
        "make": "Toyota",
        "model": "Corolla",
        "policy_number": "POL12345",
        "start_date": start_date,
        "end_date": end_date,
        "coverage": "Comprehensive"
    }
    optional_extras = [
        {"extra_id": 1, "name": "Roadside Assistance", "code": "RA001", "price": 50.0},
        {"extra_id": 3, "name": "Personal Accident Cover", "code": "PAC003", "price": -75.0}  # Invalid price
    ]
    response = client.post(
        "/create_car_insurance_policy",
        json={"policy": policy_data, "optional_extras": optional_extras},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": Messages.OPTIONAL_EXTRAS_NOT_FOUND.format(3)}


def test_create_car_insurance_policy_database_error(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database insert operation to raise an exception
    mocker.patch("app.statements.InsertStatementExecutor.execute_insert", side_effect=ValueError(APIResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR, message=Messages.DB_ERROR, data=None)))
    # Send a request to create a car insurance policy
    start_date, end_date = get_policy_dates()
    policy_data = {
        "user_id": 1,
        "vrn": "ABC123",
        "make": "Toyota",
        "model": "Corolla",
        "policy_number": "POL12345",
        "start_date": start_date,
        "end_date": end_date,
        "coverage": "Comprehensive"
    }
    optional_extras = [
        {"extra_id": 1, "name": "Roadside Assistance", "code": "RA001", "price": 50.0},
        {"extra_id": 3, "name": "Personal Accident Cover", "code": "PAC003", "price": 75.0}
    ]
    response = client.post(
        "/create_car_insurance_policy",
        json={"policy": policy_data, "optional_extras": optional_extras},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": Messages.DB_ERROR}

def test_read_car_insurance_policy_list_all_admin(admin_token, mocker, valid_admin_user, mock_policies, mock_policies_with_extras):
    patch_user_and_service(mocker, valid_admin_user, mock_policies, mock_policies_with_extras)
    response = client.get("/read_car_insurance_policy", params={"mode": "list_all"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["message"] == Messages.POLICY_READ_SUCCESS
    assert data["policies"] == mock_policies_with_extras

def test_read_car_insurance_policy_by_id_admin(admin_token, mocker, valid_admin_user, mock_policies, mock_policies_with_extras):
    patch_user_and_service(mocker, valid_admin_user, mock_policies, mock_policies_with_extras)
    response = client.get("/read_car_insurance_policy", params={"mode": "by_id", "policy_id": 1}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["message"] == Messages.POLICY_READ_SUCCESS
    assert data["policies"] == mock_policies_with_extras

def test_read_car_insurance_policy_myself_non_admin(non_admin_token, mocker, valid_non_admin_user, mock_policies, mock_policies_with_extras):
    patch_user_and_service(mocker, valid_non_admin_user, mock_policies, mock_policies_with_extras)
    response = client.get("/read_car_insurance_policy", params={"mode": "myself"}, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["message"] == Messages.POLICY_READ_SUCCESS
    assert data["policies"] == mock_policies_with_extras

def test_read_car_insurance_policy_filter_admin(admin_token, mocker, valid_admin_user, mock_policies, mock_policies_with_extras):
    patch_user_and_service(mocker, valid_admin_user, mock_policies, mock_policies_with_extras)
    response = client.get("/read_car_insurance_policy", params={"mode": "filter", "field": "make", "value": "Toyota"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["message"] == Messages.POLICY_READ_SUCCESS
    assert data["policies"] == mock_policies_with_extras

def test_read_car_insurance_policy_missing_mode(admin_token):
    response = client.get("/read_car_insurance_policy", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "mode" in response.text

def test_read_car_insurance_policy_by_id_missing_policy_id(admin_token):
    response = client.get("/read_car_insurance_policy", params={"mode": "by_id"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "policy_id" in response.text

def test_read_car_insurance_policy_filter_missing_field(admin_token):
    response = client.get("/read_car_insurance_policy", params={"mode": "filter"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "field" in response.text

def test_read_car_insurance_policy_invalid_mode(admin_token):
    response = client.get("/read_car_insurance_policy", params={"mode": "invalid"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Invalid mode" in response.text

def test_read_car_insurance_policy_non_admin_forbidden(non_admin_token, mocker, valid_non_admin_user):
    # Mock the User class to simulate
    # the requesting non-admin user
    #check admin should throw value error which becomes 403 httpexception
    # dosent get to quering db
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    response = client.get("/read_car_insurance_policy", params={"mode": "list_all"}, headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION}

def test_read_car_insurance_policy_database_error(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate
    # the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock the database query operation to raise an exception
    mocker.patch("app.statements.SelectStatementExecutor.execute_select", side_effect=ValueError(APIResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR, message=Messages.DB_ERROR, data=None)))
    # Send a request to read car insurance policies
    response = client.get("/read_car_insurance_policy", params={"mode": "list_all"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": Messages.DB_ERROR}

def test_update_car_insurance_policy_valid_admin(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock user lookup and permission check
    mocker.patch("app.services.user_service.UserService.get_user_by_id", return_value=valid_admin_user)
    mocker.patch("app.services.user_service.UserService.check_update_permissions", return_value=True)
    # Mock the database update operation
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", return_value=None)
    # Mock the CarInsurancePolicyService
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.update_car_insurance_policy", return_value=None)

    policy_data = {
        "ci_policy_id": 1,
        "user_id": 1,
        "vrn": "ABC123",
        "make": "Toyota",
        "model": "Corolla",
        "policy_number": "POL12345",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "coverage": "Comprehensive"
    }
    optional_extras = [
        {"extra_id": 1, "name": "Roadside Assistance", "code": "RA001", "price": 50.0}
    ]
    response = client.put(
        "/update_car_insurance_policy",
        json={"updated_policy": policy_data, "optional_extras": optional_extras},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["message"] == Messages.POLICY_UPDATED_SUCCESS
    assert data["policy"]["policy_number"] == "POL12345"
    assert data["optional_extras"][0]["name"] == "Roadside Assistance"

def test_update_car_insurance_policy_valid_non_admin(non_admin_token, mocker, valid_non_admin_user):
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    mocker.patch("app.services.user_service.UserService.get_user_by_id", return_value=valid_non_admin_user)
    mocker.patch("app.services.user_service.UserService.check_update_permissions", return_value=True)
    mocker.patch("app.statements.UpdateStatementExecutor.execute_update", return_value=None)
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.update_car_insurance_policy", return_value=None)

    policy_data = {
        "ci_policy_id": 2,
        "user_id": 2,
        "vrn": "XYZ789",
        "make": "Honda",
        "model": "Civic",
        "policy_number": "POL67890",
        "start_date": "2025-02-01",
        "end_date": "2026-01-31",
        "coverage": "Third Party"
    }
    response = client.put(
        "/update_car_insurance_policy",
        json={"updated_policy": policy_data},
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["message"] == Messages.POLICY_UPDATED_SUCCESS
    assert data["policy"]["policy_number"] == "POL67890"

def test_update_car_insurance_policy_forbidden(non_admin_token, mocker, valid_non_admin_user):
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    mocker.patch("app.services.user_service.UserService.get_user_by_id", return_value=valid_non_admin_user)
    # Simulate permission denied
    mocker.patch("app.services.user_service.UserService.check_update_permissions", return_value=False)
    policy_data = {
        "ci_policy_id": 1,
        "user_id": 1,  # Not the same as non-admin user
        "vrn": "ABC123",
        "make": "Toyota",
        "model": "Corolla",
        "policy_number": "POL12345",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "coverage": "Comprehensive"
    }
    response = client.put(
        "/update_car_insurance_policy",
        json={"updated_policy": policy_data},
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert response.status_code == HTTPStatus.FORBIDDEN

def test_update_car_insurance_policy_invalid_data(admin_token, mocker, valid_admin_user):
    mocker.patch("app.main.User", return_value=valid_admin_user)
    mocker.patch("app.services.user_service.UserService.get_user_by_id", return_value=valid_admin_user)
    mocker.patch("app.services.user_service.UserService.check_update_permissions", return_value=True)
    # Invalid because policy_number contains a space
    policy_data = {
        "ci_policy_id": 1,
        "user_id": 1,
        "vrn": "ABC123",
        "make": "Toyota",
        "model": "Corolla",
        "policy_number": "POL 12345",  # Invalid
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "coverage": "Comprehensive"
    }
    response = client.put(
        "/update_car_insurance_policy",
        json={"updated_policy": policy_data},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_update_car_insurance_policy_database_error(admin_token, mocker, valid_admin_user):
    mocker.patch("app.main.User", return_value=valid_admin_user)
    mocker.patch("app.services.user_service.UserService.get_user_by_id", return_value=valid_admin_user)
    mocker.patch("app.services.user_service.UserService.check_update_permissions", return_value=True)
    # Simulate DB error
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.update_car_insurance_policy", side_effect=Exception("DB error"))
    policy_data = {
        "ci_policy_id": 1,
        "user_id": 1,
        "vrn": "ABC123",
        "make": "Toyota",
        "model": "Corolla",
        "policy_number": "POL12345",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "coverage": "Comprehensive"
    }
    response = client.put(
        "/update_car_insurance_policy",
        json={"updated_policy": policy_data},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert Messages.DB_ERROR in response.text

def test_update_car_insurance_policy_missing_policy(admin_token):
    # Missing updated_policy in request body
    response = client.put(
        "/update_car_insurance_policy",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_delete_car_insurance_policy_valid_admin(admin_token, mocker, valid_admin_user):
    # Mock the User class to simulate the requesting admin user
    mocker.patch("app.main.User", return_value=valid_admin_user)
    # Mock user lookup and admin check
    mocker.patch("app.services.user_service.UserService.get_user_by_id", return_value=valid_admin_user)
    mocker.patch("app.services.user_service.UserService.check_admin", return_value=True)
    # Mock CarInsurancePolicyService methods
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.check_car_insurance_policy_exists", return_value=None)
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.delete_car_insurance_policy", return_value=1)

    response = client.delete(
        "/delete_car_insurance_policy",
        params={"policy_id": 1},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["message"] == Messages.POLICY_DELETED_SUCCESS
    assert data["policy_id"] == 1

def test_delete_car_insurance_policy_non_admin_forbidden(non_admin_token, mocker, valid_non_admin_user):
    mocker.patch("app.main.User", return_value=valid_non_admin_user)
    mocker.patch("app.services.user_service.UserService.get_user_by_id", return_value=valid_non_admin_user)
    # Simulate admin check raising ValueError (forbidden)
    mocker.patch("app.services.user_service.UserService.check_admin", side_effect=ValueError(APIResponse(status=HTTPStatus.FORBIDDEN, message=Messages.USER_NO_PERMISSION, data=None)))
    response = client.delete(
        "/delete_car_insurance_policy",
        params={"policy_id": 1},
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": Messages.USER_NO_PERMISSION}

def test_delete_car_insurance_policy_not_found(admin_token, mocker, valid_admin_user):
    mocker.patch("app.main.User", return_value=valid_admin_user)
    mocker.patch("app.services.user_service.UserService.get_user_by_id", return_value=valid_admin_user)
    mocker.patch("app.services.user_service.UserService.check_admin", return_value=True)
    # Simulate policy not found
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.check_car_insurance_policy_exists", side_effect=ValueError(APIResponse(status=HTTPStatus.NOT_FOUND, message=Messages.POLICY_NOT_FOUND, data=None)))
    response = client.delete(
        "/delete_car_insurance_policy",
        params={"policy_id": 999},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": Messages.POLICY_NOT_FOUND}

def test_delete_car_insurance_policy_database_error(admin_token, mocker, valid_admin_user):
    mocker.patch("app.main.User", return_value=valid_admin_user)
    mocker.patch("app.services.user_service.UserService.get_user_by_id", return_value=valid_admin_user)
    mocker.patch("app.services.user_service.UserService.check_admin", return_value=True)
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.check_car_insurance_policy_exists", return_value=None)
    # Simulate DB error on delete
    mocker.patch("app.services.car_insurance_policy_service.CarInsurancePolicyService.delete_car_insurance_policy", side_effect=Exception("DB error"))
    response = client.delete(
        "/delete_car_insurance_policy",
        params={"policy_id": 1},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert Messages.DB_ERROR in response.text

def test_delete_car_insurance_policy_missing_policy_id(admin_token):
    response = client.delete(
        "/delete_car_insurance_policy",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "policy_id" in response.text

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"

# This test must stay last in the file as it reloads the app.main module
# and will affect all other tests if run before this one.
def test_secret_key_not_set_in_env(mocker):
    # Mock os.getenv to return None for SECRET_KEY
    mocker.patch("os.getenv", return_value=None)

    # Reload the app.main module to re-trigger the SECRET_KEY check
    with pytest.raises(RuntimeError) as exc_info:
        import app.main
        importlib.reload(app.main)  # Reload the module to apply the mock
    assert str(exc_info.value) == "SECRET_KEY is not set in the environment variables"