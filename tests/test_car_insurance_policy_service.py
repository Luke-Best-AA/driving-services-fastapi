import pytest
from app.services.car_insurance_policy_service import CarInsurancePolicyService
from app.services.user_service import UserService
from app.models.car_insurance_policy import CarInsurancePolicy
from app.models.optional_extra import OptionalExtra
from app.models.user import User
from app.utils.messages import Messages

@pytest.fixture
def mock_cursor(mocker):
    cursor = mocker.Mock()
    cursor.commit = mocker.Mock()
    cursor.rollback = mocker.Mock()
    return cursor

@pytest.fixture
def admin_user():
    return User(user_id=1, username="admin", password="", email="admin@example.com", is_admin=True)

@pytest.fixture
def non_admin_user():
    return User(user_id=2, username="user", password="", email="user@example.com", is_admin=False)

@pytest.fixture
def policy():
    return CarInsurancePolicy(
        ci_policy_id=1,
        user_id=1,
        vrn="ABC123",
        make="Toyota",
        model="Corolla",
        policy_number="POL12345",
        start_date="2025-01-01",
        end_date="2025-12-31",
        coverage="Comprehensive"
    )

@pytest.fixture
def optional_extras():
    return [
        OptionalExtra(extra_id=1, name="Roadside Assistance", code="RA001", price=50.0),
        OptionalExtra(extra_id=2, name="Personal Accident", code="PA002", price=75.0)
    ]

@pytest.mark.asyncio
async def test_create_car_insurance_policy_success(mocker, mock_cursor, admin_user, policy, optional_extras):
    mocker.patch("app.services.user_service.UserService", autospec=True)
    mocker.patch("app.services.car_insurance_policy_service.InsertStatementExecutor.execute_insert", return_value=101)
    mocker.patch("app.services.car_insurance_policy_service.InsertStatementExecutor.execute_insert_many", return_value=None)
    mocker.patch.object(CarInsurancePolicyService, "compare_valid_optional_extras", return_value=None)
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy, optional_extras)
    policy_id = await service.create_car_insurance_policy()
    assert policy_id == 101
    mock_cursor.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_car_insurance_policy_success(mocker, mock_cursor, admin_user, policy, optional_extras):
    mocker.patch("app.services.user_service.UserService", autospec=True)
    mocker.patch.object(CarInsurancePolicyService, "check_car_insurance_policy_exists", return_value=None)
    mocker.patch.object(CarInsurancePolicyService, "check_user_update_permissions", return_value=None)
    mocker.patch.object(CarInsurancePolicyService, "compare_valid_optional_extras", return_value=None)
    mocker.patch.object(CarInsurancePolicyService, "perform_update", return_value=None)
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy, optional_extras)
    await service.update_car_insurance_policy()
    mock_cursor.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_car_insurance_policy_success(mocker, mock_cursor, admin_user, policy):
    mocker.patch("app.services.user_service.UserService", autospec=True)
    mocker.patch("app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select", return_value=[])
    mocker.patch("app.services.car_insurance_policy_service.DeleteStatementExecutor.execute_delete", return_value=None)
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy)
    result = await service.delete_car_insurance_policy()
    assert result == policy.ci_policy_id

@pytest.mark.asyncio
async def test_list_all_car_insurance_policies_admin(mocker, mock_cursor, admin_user, policy):
    mocker.patch("app.services.user_service.UserService.check_admin", return_value=True)
    mocker.patch("app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select", return_value=[policy.model_dump()])
    mocker.patch.object(CarInsurancePolicyService, "format_car_insurance_policies", return_value=[policy])
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy)
    result = await service.list_all_car_insurance_policies()
    assert result == [policy]

@pytest.mark.asyncio
async def test_get_policy_extras(mocker, mock_cursor, admin_user, policy, optional_extras):
    mocker.patch("app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select", return_value=[extra.model_dump() for extra in optional_extras])
    mocker.patch("app.services.optional_extra_service.OptionalExtraService.format_optional_extras", side_effect=lambda x: x)
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy)
    result = await service.get_policy_extras([policy])
    assert result[0]["policy"]["ci_policy_id"] == policy.ci_policy_id
    assert result[0]["optional_extras"] == [extra.model_dump() for extra in optional_extras]

@pytest.mark.asyncio
async def test_compare_valid_optional_extras_success(mocker, mock_cursor, admin_user, policy, optional_extras):
    mocker.patch("app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select", return_value=[extra.model_dump() for extra in optional_extras])
    mocker.patch("app.services.optional_extra_service.OptionalExtraService.format_optional_extras", side_effect=lambda x: x)
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy, optional_extras)
    extra_ids = [extra.extra_id for extra in optional_extras]  # <-- FIX HERE
    result = await service.compare_valid_optional_extras(extra_ids)
    # The method doesn't return extras, just None if all are valid, or raises if not
    assert result is None

@pytest.mark.asyncio
async def test_compare_valid_optional_extras_invalid(mocker, mock_cursor, admin_user, policy):
    mocker.patch("app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select", return_value=[])
    mocker.patch("app.services.optional_extra_service.OptionalExtraService.format_optional_extras", side_effect=lambda x: x)
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy)
    invalid_extra_ids = [999]
    with pytest.raises(ValueError) as exc:
        await service.compare_valid_optional_extras(invalid_extra_ids)
    assert Messages.OPTIONAL_EXTRAS_NOT_FOUND.format("999") in str(exc.value)

@pytest.mark.asyncio
async def test_check_car_insurance_policy_exists_success(mocker, mock_cursor, admin_user, policy, optional_extras):
    # Mock get_car_insurance_policy_by_id to return a valid policy dict
    mocker.patch.object(
        CarInsurancePolicyService,
        "get_car_insurance_policy_by_id",
        return_value=[policy.model_dump()]
    )
    # Mock the extras query to return only OptionalExtra fields
    mocker.patch(
        "app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select",
        return_value=[extra.model_dump() for extra in optional_extras]
    )
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy)
    await service.check_car_insurance_policy_exists()
    assert isinstance(service.current_policy, CarInsurancePolicy)
    assert isinstance(service.current_optional_extras, list)
    assert all(isinstance(e, OptionalExtra) for e in service.current_optional_extras)

@pytest.mark.asyncio
async def test_perform_update_no_changes(mocker, mock_cursor, admin_user, policy, optional_extras):
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy, optional_extras)
    # Set current_policy and current_optional_extras to match new ones (no changes)
    service.current_policy = policy
    service.current_optional_extras = optional_extras
    with pytest.raises(ValueError) as exc:
        await service.perform_update()
    assert "No changes detected" in str(exc.value)

@pytest.mark.asyncio
async def test_perform_update_policy_changed(mocker, mock_cursor, admin_user, policy, optional_extras):
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy, optional_extras)
    # Set current_policy to a different policy (simulate change)
    changed_policy = CarInsurancePolicy(
        ci_policy_id=1,
        user_id=1,
        vrn="XYZ999",
        make="Toyota",
        model="Corolla",
        policy_number="POL12345",
        start_date="2025-01-01",
        end_date="2025-12-31",
        coverage="Comprehensive"
    )
    service.current_policy = changed_policy
    service.current_optional_extras = optional_extras
    mocker.patch("app.services.car_insurance_policy_service.UpdateStatementExecutor.execute_update", return_value=None)
    # update_optional_extras should not be called since optional_extras didn't change
    mocker.patch.object(service, "update_optional_extras", return_value=None)
    await service.perform_update()

@pytest.mark.asyncio
async def test_perform_update_optional_extras_changed(mocker, mock_cursor, admin_user, policy, optional_extras):
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy, optional_extras)
    # Set current_optional_extras to something different
    service.current_policy = policy
    service.current_optional_extras = []
    mocker.patch("app.services.car_insurance_policy_service.UpdateStatementExecutor.execute_update", return_value=None)
    mock_update_extras = mocker.patch.object(service, "update_optional_extras", return_value=None)
    await service.perform_update()
    mock_update_extras.assert_called_once()

@pytest.mark.asyncio
async def test_update_optional_extras_add_and_remove(mocker, mock_cursor, admin_user, policy, optional_extras):
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy, optional_extras)
    # Mock compare_valid_optional_extras to do nothing
    mocker.patch.object(service, "compare_valid_optional_extras", return_value=None)
    # Mock current_extras to simulate DB state
    mocker.patch(
        "app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select",
        return_value=[{"extra_id": 1}]
    )
    # Patch add/remove methods
    mock_add = mocker.patch.object(service, "add_optional_extras", return_value=None)
    mock_remove = mocker.patch.object(service, "remove_optional_extras", return_value=None)
    await service.update_optional_extras()
    # Should add extra_id=2 and remove extra_id=1 if optional_extras=[1,2] and current_extras=[1]
    mock_add.assert_called_once()
    mock_remove.assert_not_called()  # Only add is needed if new_extras is superset

@pytest.mark.asyncio
async def test_update_optional_extras_remove_only(mocker, mock_cursor, admin_user, policy):
    # Only current_extras exist, no new extras
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy, optional_extras=[])
    mocker.patch.object(service, "compare_valid_optional_extras", return_value=None)
    mocker.patch(
        "app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select",
        return_value=[{"extra_id": 1}]
    )
    mock_add = mocker.patch.object(service, "add_optional_extras", return_value=None)
    mock_remove = mocker.patch.object(service, "remove_optional_extras", return_value=None)
    await service.update_optional_extras()
    mock_add.assert_not_called()
    mock_remove.assert_called_once()

@pytest.mark.asyncio
async def test_delete_car_insurance_policy_removes_extras(mocker, mock_cursor, admin_user, policy, optional_extras):
    # Patch SelectStatementExecutor.execute_select to return extras (simulate extras exist)
    mocker.patch(
        "app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select",
        return_value=[extra.model_dump() for extra in optional_extras]
    )
    # Patch remove_optional_extras and DeleteStatementExecutor.execute_delete
    mock_remove = mocker.patch.object(
        CarInsurancePolicyService, "remove_optional_extras", return_value=None
    )
    mocker.patch(
        "app.services.car_insurance_policy_service.DeleteStatementExecutor.execute_delete",
        return_value=None
    )
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy)
    await service.delete_car_insurance_policy()
    mock_remove.assert_called_once_with(policy.ci_policy_id, [extra.extra_id for extra in optional_extras])    

@pytest.mark.asyncio
async def test_get_car_insurance_policy_by_id_forbidden(mocker, mock_cursor, policy):
    user = User(user_id=2, username="user", password="", email="user@example.com", is_admin=False)
    service = CarInsurancePolicyService(mock_cursor, user, policy)
    # Patch check_user_owns_policy to return False
    mocker.patch.object(service.user_service, "check_user_owns_policy", return_value=False)
    with pytest.raises(ValueError) as exc:
        await service.get_car_insurance_policy_by_id(policy.ci_policy_id)
    assert Messages.USER_NO_PERMISSION in str(exc.value)

@pytest.mark.asyncio
async def test_get_car_insurance_policy_by_id_not_found(mocker, mock_cursor, policy):
    user = User(user_id=1, username="admin", password="", email="admin@example.com", is_admin=True)
    service = CarInsurancePolicyService(mock_cursor, user, policy)
    # Patch execute_select to return empty list
    mocker.patch("app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select", return_value=[])
    with pytest.raises(ValueError) as exc:
        await service.get_car_insurance_policy_by_id(policy.ci_policy_id)
    assert Messages.POLICY_NOT_FOUND in str(exc.value)

@pytest.mark.asyncio
async def test_get_car_insurance_policy_by_id_success(mocker, mock_cursor, policy):
    user = User(user_id=1, username="admin", password="", email="admin@example.com", is_admin=True)
    service = CarInsurancePolicyService(mock_cursor, user, policy)
    # Patch execute_select to return a policy dict
    mocker.patch("app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select", return_value=[policy.model_dump()])
    result = await service.get_car_insurance_policy_by_id(policy.ci_policy_id)
    assert result[0]["ci_policy_id"] == policy.ci_policy_id

@pytest.mark.asyncio
async def test_get_car_insurance_policy_by_id_success_with_format(mocker, mock_cursor, policy):
    user = User(user_id=1, username="admin", password="", email="admin@example.com", is_admin=True)
    service = CarInsurancePolicyService(mock_cursor, user, policy)
    # Patch execute_select to return a policy dict
    mocker.patch("app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select", return_value=[policy.model_dump()])
    # Patch format_car_insurance_policies to return a formatted list
    mocker.patch.object(service, "format_car_insurance_policies", return_value=["formatted_policy"])
    result = await service.get_car_insurance_policy_by_id(policy.ci_policy_id, format=True)
    assert result == ["formatted_policy"]

@pytest.mark.asyncio
async def test_get_car_insurance_policy_by_user_id_forbidden(mocker, mock_cursor, policy):
    # Non-admin user, requesting policies for another user
    user = User(user_id=2, username="user", password="", email="user@example.com", is_admin=False)
    service = CarInsurancePolicyService(mock_cursor, user, policy)
    with pytest.raises(ValueError) as exc:
        await service.get_car_insurance_policy_by_user_id(999)
    assert Messages.USER_NO_PERMISSION in str(exc.value)

@pytest.mark.asyncio
async def test_get_car_insurance_policy_by_user_id_success(mocker, mock_cursor, policy):
    # Admin user, should succeed
    user = User(user_id=1, username="admin", password="", email="admin@example.com", is_admin=True)
    service = CarInsurancePolicyService(mock_cursor, user, policy)
    # Patch execute_select to return a policy dict
    mocker.patch(
        "app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select",
        return_value=[policy.model_dump()]
    )
    # Patch format_car_insurance_policies to just return a marker
    mocker.patch.object(
        service,
        "format_car_insurance_policies",
        return_value=["formatted_policy"]
    )
    result = await service.get_car_insurance_policy_by_user_id(user.user_id)
    assert result == ["formatted_policy"]

@pytest.mark.asyncio
async def test_filter_car_insurance_policies(mocker, mock_cursor, admin_user, policy):
    # Patch check_admin to do nothing (simulate admin)
    mocker.patch.object(
        UserService,
        "check_admin",
        return_value=True
    )
    # Patch execute_select to return a list of dicts
    mocker.patch(
        "app.services.car_insurance_policy_service.SelectStatementExecutor.execute_select",
        return_value=[policy.model_dump()]
    )
    # Patch format_car_insurance_policies to just return a marker
    mock_format = mocker.patch.object(
        CarInsurancePolicyService,
        "format_car_insurance_policies",
        return_value=["formatted_policy"]
    )
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy)
    result = await service.filter_car_insurance_policies("make", "Toyota")
    mock_format.assert_called_once()
    assert result == ["formatted_policy"]

def test_format_car_insurance_policies(mocker, mock_cursor, admin_user, policy):
    # Prepare a list of dicts as would be returned from the DB
    policy_dict = policy.model_dump()
    # Patch dates_to_string to just pass (or check call count)
    mock_dates = mocker.patch("app.services.car_insurance_policy_service.dates_to_string")
    service = CarInsurancePolicyService(mock_cursor, admin_user, policy)
    result = service.format_car_insurance_policies([policy_dict])
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], CarInsurancePolicy)
    assert result[0].ci_policy_id == policy.ci_policy_id
    mock_dates.assert_called_once_with(policy_dict)    