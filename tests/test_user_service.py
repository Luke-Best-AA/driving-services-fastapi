import pytest
from app.services.user_service import UserService
from app.user import User
from app.messages import Messages

@pytest.fixture
def mock_cursor(mocker):
    return mocker.Mock()

@pytest.fixture
def user():
    return User(user_id=1, username="alice", password="5f4dcc3b5aa765d61d8327deb882cf99", email="alice@example.com", is_admin=True)

@pytest.mark.asyncio
async def test_get_user_by_id_success(mocker, mock_cursor, user):
    mocker.patch(
        "app.services.user_service.SelectStatementExecutor.execute_select",
        return_value=[user.model_dump()]
    )
    service = UserService(mock_cursor)
    result = await service.get_user_by_id(user.user_id, requesting_user=user)
    assert isinstance(result, User)
    assert result.user_id == user.user_id

@pytest.mark.asyncio
async def test_get_user_by_id_forbidden(mocker, mock_cursor, user):
    other_user = User(user_id=2, username="bob", password="", email="bob@example.com", is_admin=False)
    service = UserService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        await service.get_user_by_id(user.user_id, requesting_user=other_user)
    assert Messages.USER_NO_PERMISSION in str(exc.value)

@pytest.mark.asyncio
async def test_get_user_by_id_not_found(mocker, mock_cursor, user):
    mocker.patch(
        "app.services.user_service.SelectStatementExecutor.execute_select",
        return_value=[]
    )
    service = UserService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        await service.get_user_by_id(user.user_id, requesting_user=user)
    assert Messages.USER_NOT_FOUND in str(exc.value)

@pytest.mark.asyncio
async def test_authenticate_user_success(mocker, mock_cursor, user):
    mocker.patch(
        "app.services.user_service.SelectStatementExecutor.execute_select",
        return_value=[user.model_dump()]
    )
    service = UserService(mock_cursor)
    result = await service.authenticate_user(user.username, user.password)
    assert isinstance(result, User)
    assert result.username == user.username

@pytest.mark.asyncio
async def test_authenticate_user_invalid(mocker, mock_cursor):
    mocker.patch(
        "app.services.user_service.SelectStatementExecutor.execute_select",
        return_value=[]
    )
    service = UserService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        await service.authenticate_user("baduser", "badpass")
    assert Messages.USER_INVALID_CREDENTIALS in str(exc.value)

@pytest.mark.asyncio
async def test_create_user(mocker, mock_cursor, user):
    mocker.patch(
        "app.services.user_service.InsertStatementExecutor.execute_insert",
        return_value=42
    )
    service = UserService(mock_cursor)
    result = await service.create_user(user)
    assert result.user_id == 42
    assert result.password is None

@pytest.mark.asyncio
async def test_update_user_success(mocker, mock_cursor, user):
    mocker.patch.object(
        UserService,
        "get_user_by_id",
        return_value=user
    )
    mock_update = mocker.patch(
        "app.services.user_service.UpdateStatementExecutor.execute_update",
        return_value=None
    )
    service = UserService(mock_cursor)
    updated = User(user_id=1, username="alice2", password="", email="alice2@example.com", is_admin=True)
    await service.update_user(updated)
    mock_update.assert_called_once()

@pytest.mark.asyncio
async def test_update_user_no_change(mocker, mock_cursor, user):
    mocker.patch.object(
        UserService,
        "get_user_by_id",
        return_value=user
    )
    service = UserService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        await service.update_user(user)
    assert Messages.NO_CHANGE in str(exc.value)

@pytest.mark.asyncio
async def test_update_user_not_found(mocker, mock_cursor, user):
    mocker.patch.object(
        UserService,
        "get_user_by_id",
        return_value=None
    )
    service = UserService(mock_cursor)
    updated = User(user_id=999, username="ghost", password="", email="ghost@example.com", is_admin=False)
    with pytest.raises(ValueError) as exc:
        await service.update_user(updated)
    assert Messages.USER_NOT_FOUND in str(exc.value)

@pytest.mark.asyncio
async def test_delete_user_success(mocker, mock_cursor, user):
    mocker.patch.object(
        UserService,
        "get_user_by_id",
        return_value=user
    )
    mock_delete = mocker.patch(
        "app.services.user_service.DeleteStatementExecutor.execute_delete",
        return_value=None
    )
    service = UserService(mock_cursor)
    await service.delete_user(user.user_id)
    mock_delete.assert_called_once()

@pytest.mark.asyncio
async def test_delete_user_not_found(mocker, mock_cursor):
    mocker.patch.object(
        UserService,
        "get_user_by_id",
        return_value=None
    )
    service = UserService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        await service.delete_user(999)
    assert Messages.USER_NOT_FOUND in str(exc.value)

def test_check_admin_success(mock_cursor, user):
    service = UserService(mock_cursor)
    assert service.check_admin(user) is True

def test_check_admin_forbidden(mock_cursor):
    user = User(user_id=2, username="bob", password="", email="bob@example.com", is_admin=False)
    service = UserService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        service.check_admin(user)
    assert Messages.USER_NO_PERMISSION in str(exc.value)

def test_check_update_permissions_admin(mock_cursor, user):
    service = UserService(mock_cursor)
    assert service.check_update_permissions(user, 1) is True

def test_check_update_permissions_self(mock_cursor):
    user = User(user_id=2, username="bob", password="", email="bob@example.com", is_admin=False)
    service = UserService(mock_cursor)
    assert service.check_update_permissions(user, 2) is True

def test_check_update_permissions_forbidden(mock_cursor):
    user = User(user_id=2, username="bob", password="", email="bob@example.com", is_admin=False)
    service = UserService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        service.check_update_permissions(user, 1)
    assert Messages.USER_NO_PERMISSION_CHANGE in str(exc.value)

def test_check_update_permissions_no_exception(mocker, mock_cursor):
    user = User(user_id=2, username="bob", password="", email="bob@example.com", is_admin=False)
    service = UserService(mock_cursor)
    result = service.check_update_permissions(user, 1, throw_exception=False)
    assert result is False

@pytest.mark.asyncio
async def test_check_user_owns_policy_true(mocker, mock_cursor, user):
    mocker.patch(
        "app.services.user_service.SelectStatementExecutor.execute_select",
        return_value=[{"ci_policy_id": 1, "user_id": user.user_id}]
    )
    service = UserService(mock_cursor)
    result = await service.check_user_owns_policy(user, 1)
    assert result is True

@pytest.mark.asyncio
async def test_check_user_owns_policy_false(mocker, mock_cursor, user):
    mocker.patch(
        "app.services.user_service.SelectStatementExecutor.execute_select",
        return_value=[]
    )
    service = UserService(mock_cursor)
    result = await service.check_user_owns_policy(user, 1)
    assert result is False

@pytest.mark.asyncio
async def test_list_all_users_success(mocker, mock_cursor, user):
    mocker.patch.object(UserService, "check_admin", return_value=True)
    mocker.patch(
        "app.services.user_service.SelectStatementExecutor.execute_select",
        return_value=[user.model_dump()]
    )
    mocker.patch.object(UserService, "format_users", return_value=["formatted_user"])
    service = UserService(mock_cursor)
    result = await service.list_all_users(user)
    assert result == ["formatted_user"]

@pytest.mark.asyncio
async def test_filter_users_success(mocker, mock_cursor, user):
    mocker.patch.object(UserService, "check_admin", return_value=True)
    mocker.patch(
        "app.services.user_service.SelectStatementExecutor.execute_select",
        return_value=[user.model_dump()]
    )
    mocker.patch.object(UserService, "format_users", return_value=["formatted_user"])
    service = UserService(mock_cursor)
    result = await service.filter_users(user, "username", "alice")
    assert result == ["formatted_user"]

@pytest.mark.asyncio
async def test_filter_users_invalid_field(mocker, mock_cursor, user):
    mocker.patch.object(UserService, "check_admin", return_value=True)
    service = UserService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        await service.filter_users(user, "notafield", "value")
    assert "notafield" in str(exc.value)

@pytest.mark.asyncio
async def test_filter_users_not_found(mocker, mock_cursor, user):
    mocker.patch.object(UserService, "check_admin", return_value=True)
    mocker.patch(
        "app.services.user_service.SelectStatementExecutor.execute_select",
        return_value=[]
    )
    service = UserService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        await service.filter_users(user, "username", "ghost")
    assert Messages.USER_NOT_FOUND in str(exc.value)

def test_format_users(user):
    service = UserService(None)
    users = [user.model_dump()]
    result = service.format_users(users)
    assert isinstance(result, list)
    assert result[0]["user_id"] == user.user_id

@pytest.mark.asyncio
async def test_update_user_password_success(mocker, mock_cursor, user):
    # Mock get_user_by_id to return a user (user exists)
    mocker.patch.object(
        UserService,
        "get_user_by_id",
        return_value=user
    )
    mock_update = mocker.patch(
        "app.services.user_service.UpdateStatementExecutor.execute_update",
        return_value=None
    )
    service = UserService(mock_cursor)
    await service.update_user_password(user.user_id, "newpassword")
    mock_update.assert_called_once_with("UPDATE Users SET password = ? WHERE user_id = ?", ("newpassword", user.user_id))

@pytest.mark.asyncio
async def test_update_user_password_user_not_found(mocker, mock_cursor, user):
    # Mock get_user_by_id to return None (user does not exist)
    mocker.patch.object(
        UserService,
        "get_user_by_id",
        return_value=None
    )
    service = UserService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        await service.update_user_password(999, "newpassword")
    assert Messages.USER_NOT_FOUND in str(exc.value)
    
def test_verify_password_match(mock_cursor):
    service = UserService(mock_cursor)
    existing_password = "secret123"
    provided_password = "secret123"
    assert service.verify_password(existing_password, provided_password) is True

def test_verify_password_no_match(mock_cursor):
    service = UserService(mock_cursor)
    existing_password = "secret123"
    provided_password = "wrongpass"
    assert service.verify_password(existing_password, provided_password) is False

def test_verify_password_empty_strings(mock_cursor):
    service = UserService(mock_cursor)
    existing_password = ""
    provided_password = ""
    assert service.verify_password(existing_password, provided_password) is True

def test_verify_password_none_and_string(mock_cursor):
    service = UserService(mock_cursor)
    existing_password = None
    provided_password = "something"
    assert service.verify_password(existing_password, provided_password) is False

def test_verify_password_string_and_none(mock_cursor):
    service = UserService(mock_cursor)
    existing_password = "something"
    provided_password = None
    assert service.verify_password(existing_password, provided_password) is False

def test_verify_password_both_none(mock_cursor):
    service = UserService(mock_cursor)
    existing_password = None
    provided_password = None
    assert service.verify_password(existing_password, provided_password) is True
