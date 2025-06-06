from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from http import HTTPStatus

from app.models.car_insurance_policy import CarInsurancePolicy
from app.models.optional_extra import OptionalExtra
from app.utils.response import APIResponse
from app.utils.debug import Debug
from app.utils.messages import Messages
from app.utils.db_connect import DBConnect
from app.services.car_insurance_policy_service import CarInsurancePolicyService
from app.services.user_service import UserService
from app.utils.common import validate_required_fields, exception_handler, verify_token
from app.utils.config import (
    SERVER, DATABASE, DB_USERNAME, DB_PASSWORD, TRUSTED_CONNECTION
)

router = APIRouter()

@router.post("/create_car_insurance_policy")
@exception_handler
async def create_car_insurance_policy(
    policy: CarInsurancePolicy,
    optional_extras: list[OptionalExtra] = None,
    token_data: dict = Depends(verify_token)
):
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        user_service = UserService(cursor)
        requesting_user = await user_service.get_user_by_id(token_data["user_id"])
        if not requesting_user.is_admin and policy.user_id != requesting_user.user_id:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.FORBIDDEN,
                    message=Messages.USER_NO_PERMISSION,
                    data=None
                )
            )   
        validate_required_fields({"policy": policy})
        await policy.validate_car_insurance_policy_values()           
        service = CarInsurancePolicyService(cursor, requesting_user, policy, optional_extras)
        policy_id = await service.create_car_insurance_policy()
        policy.ci_policy_id = policy_id

    return JSONResponse(
        content={
            "message": Messages.POLICY_CREATED_SUCCESS,
            "policy": policy.model_dump(),
            "optional_extras": [extra.model_dump() for extra in optional_extras] if optional_extras else None
        },
        status_code=HTTPStatus.CREATED
    )

@router.get("/read_car_insurance_policy")
@exception_handler
async def read_car_insurance_policy(
    mode: str,
    policy_id: int = None,
    field: str = None,
    value: str = None,
    token_data: dict = Depends(verify_token)
):
    required_fields = {
        "mode": mode,
    }
    if mode == "by_id":
        required_fields["policy_id"] = policy_id
    elif mode == "filter":
        required_fields["field"] = field
        required_fields["value"] = value
    validate_required_fields(required_fields)

    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        user_service = UserService(cursor)
        requesting_user = await user_service.get_user_by_id(token_data["user_id"])
        service = CarInsurancePolicyService(cursor, requesting_user, None, None)

        if mode == "list_all":
            policies = await service.list_all_car_insurance_policies()
        elif mode == "by_id":
            policies = await service.get_car_insurance_policy_by_id(policy_id, format=True)
        elif mode == "myself":
            policies = await service.get_car_insurance_policy_by_user_id(requesting_user.user_id)
        elif mode == "filter":
            policies = await service.filter_car_insurance_policies(field, value)
        else:
            raise ValueError("Invalid mode. Use 'list_all', 'by_id', 'myself' or 'filter'.")

        policies_with_extras = await service.get_policy_extras(policies)

    return JSONResponse(
        content={
            "message": Messages.POLICY_READ_SUCCESS,
            "policies": policies_with_extras
        },
        status_code=HTTPStatus.OK
    )

@router.put("/update_car_insurance_policy")
@exception_handler
async def update_car_insurance_policy(
    updated_policy: CarInsurancePolicy,
    optional_extras: list[OptionalExtra] = None,
    token_data: dict = Depends(verify_token)
):
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        user_service = UserService(cursor)
        requesting_user = await user_service.get_user_by_id(token_data["user_id"])
        can_update = user_service.check_update_permissions(requesting_user, updated_policy.user_id, throw_exception=False)
        validate_required_fields({"updated_policy": updated_policy})
        await updated_policy.validate_car_insurance_policy_values()

        service = CarInsurancePolicyService(cursor, requesting_user, updated_policy, optional_extras, can_update)
        await service.update_car_insurance_policy()

    return JSONResponse(
        content={
            "message": Messages.POLICY_UPDATED_SUCCESS,
            "policy": updated_policy.model_dump(),
            "optional_extras": [extra.model_dump() for extra in optional_extras] if optional_extras else None
        },
        status_code=HTTPStatus.OK
    )

@router.delete("/delete_car_insurance_policy")
@exception_handler
async def delete_car_insurance_policy(
    policy_id: int,
    token_data: dict = Depends(verify_token)
):
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        user_service = UserService(cursor)
        requesting_user = await user_service.get_user_by_id(token_data["user_id"])
        user_service.check_admin(requesting_user)
        policy = CarInsurancePolicy(ci_policy_id=policy_id, user_id=0, vrn="", make="", model="", policy_number="", start_date="", end_date="", coverage="")
        service = CarInsurancePolicyService(cursor, requesting_user, policy, None)

        await service.check_car_insurance_policy_exists()
        policy_id = await service.delete_car_insurance_policy()

    return JSONResponse(
        content={
            "message": Messages.POLICY_DELETED_SUCCESS,
            "policy_id": policy_id
        },
        status_code=HTTPStatus.OK
    )
