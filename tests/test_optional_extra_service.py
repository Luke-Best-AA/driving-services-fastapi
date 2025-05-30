import pytest
from app.services.optional_extra_service import OptionalExtraService
from app.optional_extra import OptionalExtra
from app.messages import Messages

@pytest.fixture
def mock_cursor(mocker):
    cursor = mocker.Mock()
    return cursor

@pytest.fixture
def optional_extra():
    return OptionalExtra(extra_id=1, name="Roadside Assistance", code="RA001", price=50.0)

@pytest.mark.asyncio
async def test_create_optional_extra(mocker, mock_cursor, optional_extra):
    mock_insert = mocker.patch(
        "app.services.optional_extra_service.InsertStatementExecutor.execute_insert",
        return_value=42
    )
    service = OptionalExtraService(mock_cursor)
    result = await service.create_optional_extra(optional_extra)
    assert result.extra_id == 42
    mock_insert.assert_called_once()

@pytest.mark.asyncio
async def test_update_optional_extra_success(mocker, mock_cursor, optional_extra):
    # Patch get_optional_extra_by_id to return a different object (simulate change)
    mocker.patch.object(
        OptionalExtraService,
        "get_optional_extra_by_id",
        return_value=[optional_extra.model_dump()]
    )
    mock_update = mocker.patch(
        "app.services.optional_extra_service.UpdateStatementExecutor.execute_update",
        return_value=None
    )
    service = OptionalExtraService(mock_cursor)
    # Change the name to simulate an update
    updated = OptionalExtra(extra_id=1, name="New Name", code="RA001", price=50.0)
    await service.update_optional_extra(updated)
    mock_update.assert_called_once()

@pytest.mark.asyncio
async def test_update_optional_extra_no_change(mocker, mock_cursor, optional_extra):
    # Patch get_optional_extra_by_id to return the same object (no change)
    mocker.patch.object(
        OptionalExtraService,
        "get_optional_extra_by_id",
        return_value=[optional_extra.model_dump()]
    )
    service = OptionalExtraService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        await service.update_optional_extra(optional_extra)
    assert Messages.NO_CHANGE in str(exc.value)

@pytest.mark.asyncio
async def test_update_optional_extra_not_found(mocker, mock_cursor, optional_extra):
    # Patch get_optional_extra_by_id to return empty (not found)
    mocker.patch.object(
        OptionalExtraService,
        "get_optional_extra_by_id",
        return_value=[]
    )
    service = OptionalExtraService(mock_cursor)
    updated = OptionalExtra(extra_id=999, name="New Name", code="RA001", price=50.0)
    with pytest.raises(ValueError) as exc:
        await service.update_optional_extra(updated)
    assert Messages.OPTIONAL_EXTRA_NOT_FOUND in str(exc.value)

@pytest.mark.asyncio
async def test_delete_optional_extra_success(mocker, mock_cursor, optional_extra):
    # Patch get_optional_extra_by_id to return the object (exists)
    mocker.patch.object(
        OptionalExtraService,
        "get_optional_extra_by_id",
        return_value=[optional_extra.model_dump()]
    )
    # Patch execute_select for related records to return empty list (no related records)
    mocker.patch(
        "app.services.optional_extra_service.SelectStatementExecutor.execute_select",
        return_value=[]
    )
    mock_delete = mocker.patch(
        "app.services.optional_extra_service.DeleteStatementExecutor.execute_delete",
        return_value=None
    )
    service = OptionalExtraService(mock_cursor)
    await service.delete_optional_extra(optional_extra.extra_id)
    mock_delete.assert_called_once()

@pytest.mark.asyncio
async def test_delete_optional_extra_not_found(mocker, mock_cursor):
    # Patch get_optional_extra_by_id to return empty (not found)
    mocker.patch.object(
        OptionalExtraService,
        "get_optional_extra_by_id",
        return_value=[]
    )
    service = OptionalExtraService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        await service.delete_optional_extra(999)
    assert Messages.OPTIONAL_EXTRA_NOT_FOUND in str(exc.value)

@pytest.mark.asyncio
async def test_list_all_optional_extras(mocker, mock_cursor, optional_extra):
    mock_select = mocker.patch(
        "app.services.optional_extra_service.SelectStatementExecutor.execute_select",
        return_value=[optional_extra.model_dump()]
    )
    service = OptionalExtraService(mock_cursor)
    # Patch format_optional_extras to just return a marker
    mocker.patch.object(service, "format_optional_extras", return_value=["formatted_extra"])
    result = await service.list_all_optional_extras()
    assert result == ["formatted_extra"]
    mock_select.assert_called_once()

@pytest.mark.asyncio
async def test_get_optional_extra_by_id_success(mocker, mock_cursor, optional_extra):
    mock_select = mocker.patch(
        "app.services.optional_extra_service.SelectStatementExecutor.execute_select",
        return_value=[optional_extra.model_dump()]
    )
    service = OptionalExtraService(mock_cursor)
    result = await service.get_optional_extra_by_id(optional_extra.extra_id)
    assert result[0]["extra_id"] == optional_extra.extra_id
    mock_select.assert_called_once()

@pytest.mark.asyncio
async def test_get_optional_extra_by_id_not_found(mocker, mock_cursor):
    mocker.patch(
        "app.services.optional_extra_service.SelectStatementExecutor.execute_select",
        return_value=[]
    )
    service = OptionalExtraService(mock_cursor)
    with pytest.raises(ValueError) as exc:
        await service.get_optional_extra_by_id(999)
    assert Messages.OPTIONAL_EXTRA_NOT_FOUND in str(exc.value)

def test_format_optional_extras(optional_extra):
    service = OptionalExtraService(None)
    extras = [optional_extra.model_dump()]
    result = service.format_optional_extras(extras)
    assert isinstance(result, list)
    assert result[0]["extra_id"] == optional_extra.extra_id