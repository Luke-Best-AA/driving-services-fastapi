import pytest
from app.optional_extra import OptionalExtra

@pytest.fixture
def valid_optional_extra_data():
    return {
        "extra_id": 1,
        "name": "Roadside Assistance",
        "code": "RA001",
        "price": 50.0
    }

@pytest.mark.asyncio
async def test_valid_optional_extra(valid_optional_extra_data):
    extra = OptionalExtra(**valid_optional_extra_data)
    assert await extra.validate_optional_extra_values() is True

@pytest.mark.asyncio
async def test_missing_required_fields(valid_optional_extra_data):
    data = valid_optional_extra_data.copy()
    data["name"] = ""
    extra = OptionalExtra(**data)
    with pytest.raises(ValueError) as exc:
        await extra.validate_optional_extra_values()
    assert "All fields are required." in str(exc.value)

@pytest.mark.asyncio
async def test_invalid_price(valid_optional_extra_data):
    data = valid_optional_extra_data.copy()
    data["price"] = -1
    extra = OptionalExtra(**data)
    with pytest.raises(ValueError) as exc:
        await extra.validate_optional_extra_values()
    assert "Price must be a positive number." in str(exc.value)

@pytest.mark.asyncio
async def test_negative_price(valid_optional_extra_data):
    data = valid_optional_extra_data.copy()
    data["price"] = -10
    extra = OptionalExtra(**data)
    with pytest.raises(ValueError) as exc:
        await extra.validate_optional_extra_values()
    assert "Price must be a positive number." in str(exc.value)

@pytest.mark.asyncio
async def test_invalid_name(valid_optional_extra_data):
    data = valid_optional_extra_data.copy()
    data["name"] = "Roadside@Assistance"
    extra = OptionalExtra(**data)
    with pytest.raises(ValueError) as exc:
        await extra.validate_optional_extra_values()
    assert "Name must be alphanumeric and can include spaces." in str(exc.value)

@pytest.mark.asyncio
async def test_invalid_code(valid_optional_extra_data):
    data = valid_optional_extra_data.copy()
    data["code"] = "RA001!!!"
    extra = OptionalExtra(**data)
    with pytest.raises(ValueError) as exc:
        await extra.validate_optional_extra_values()
    assert "Code must be alphanumeric and less than 10 characters." in str(exc.value)

@pytest.mark.asyncio
async def test_code_too_long(valid_optional_extra_data):
    data = valid_optional_extra_data.copy()
    data["code"] = "RA00112345X"
    extra = OptionalExtra(**data)
    with pytest.raises(ValueError) as exc:
        await extra.validate_optional_extra_values()
    assert "Code must be alphanumeric and less than 10 characters." in str(exc.value)