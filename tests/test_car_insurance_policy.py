import pytest
from app.car_insurance_policy import CarInsurancePolicy

@pytest.fixture
def valid_policy_data():
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

@pytest.mark.asyncio
async def test_valid_policy(valid_policy_data):
    policy = CarInsurancePolicy(**valid_policy_data)
    assert await policy.validate_car_insurance_policy_values() is True

@pytest.mark.asyncio
async def test_missing_required_field(valid_policy_data):
    data = valid_policy_data.copy()
    data["make"] = ""
    policy = CarInsurancePolicy(**data)
    with pytest.raises(ValueError) as exc:
        await policy.validate_car_insurance_policy_values()
    assert "Required" in str(exc.value)

@pytest.mark.asyncio
async def test_invalid_vrn(valid_policy_data):
    data = valid_policy_data.copy()
    data["vrn"] = "ABC 123!"  # Not alphanumeric
    policy = CarInsurancePolicy(**data)
    with pytest.raises(ValueError) as exc:
        await policy.validate_car_insurance_policy_values()
    assert "VRN must be alphanumeric" in str(exc.value)

@pytest.mark.asyncio
async def test_invalid_make(valid_policy_data):
    data = valid_policy_data.copy()
    data["make"] = "Toyota!"  # Not alphanumeric (spaces allowed, but not '!')
    policy = CarInsurancePolicy(**data)
    with pytest.raises(ValueError) as exc:
        await policy.validate_car_insurance_policy_values()
    assert "Make must be alphanumeric" in str(exc.value)

@pytest.mark.asyncio
async def test_invalid_model(valid_policy_data):
    data = valid_policy_data.copy()
    data["model"] = "Corolla!"  # Not alphanumeric
    policy = CarInsurancePolicy(**data)
    with pytest.raises(ValueError) as exc:
        await policy.validate_car_insurance_policy_values()
    assert "Model must be alphanumeric" in str(exc.value)

@pytest.mark.asyncio
async def test_invalid_policy_number(valid_policy_data):
    data = valid_policy_data.copy()
    data["policy_number"] = "POL 12345!"  # Not alphanumeric
    policy = CarInsurancePolicy(**data)
    with pytest.raises(ValueError) as exc:
        await policy.validate_car_insurance_policy_values()
    assert "Policy number must be alphanumeric" in str(exc.value)

@pytest.mark.asyncio
async def test_invalid_coverage(valid_policy_data):
    data = valid_policy_data.copy()
    data["coverage"] = "Comprehensive!"  # Not alphanumeric
    policy = CarInsurancePolicy(**data)
    with pytest.raises(ValueError) as exc:
        await policy.validate_car_insurance_policy_values()
    assert "Coverage must be alphanumeric" in str(exc.value)

@pytest.mark.asyncio
async def test_valid_dates(valid_policy_data):
    policy = CarInsurancePolicy(**valid_policy_data)
    assert await policy.validate_car_insurance_policy_values() is True

@pytest.mark.asyncio
async def test_invalid_start_date_format(valid_policy_data):
    data = valid_policy_data.copy()
    data["start_date"] = "01-01-2025"  # Wrong format
    policy = CarInsurancePolicy(**data)
    with pytest.raises(ValueError) as exc:
        await policy.validate_car_insurance_policy_values()
    assert "Start date must be in YYYY-MM-DD format." in str(exc.value)

@pytest.mark.asyncio
async def test_invalid_end_date_format(valid_policy_data):
    data = valid_policy_data.copy()
    data["end_date"] = "31-12-2025"  # Wrong format
    policy = CarInsurancePolicy(**data)
    with pytest.raises(ValueError) as exc:
        await policy.validate_car_insurance_policy_values()
    assert "End date must be in YYYY-MM-DD format." in str(exc.value)

@pytest.mark.asyncio
async def test_start_date_after_end_date(valid_policy_data):
    data = valid_policy_data.copy()
    data["start_date"] = "2026-01-01"
    data["end_date"] = "2025-12-31"
    policy = CarInsurancePolicy(**data)
    with pytest.raises(ValueError) as exc:
        await policy.validate_car_insurance_policy_values()
    assert "Start date must be before end date." in str(exc.value)