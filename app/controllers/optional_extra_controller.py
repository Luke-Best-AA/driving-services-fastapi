from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from http import HTTPStatus

from app.models.optional_extra import OptionalExtra
from app.utils.debug import Debug
from app.utils.messages import Messages
from app.utils.db_connect import DBConnect
from app.services.optional_extra_service import OptionalExtraService
from app.services.user_service import UserService
from app.utils.common import validate_required_fields, exception_handler, verify_token
from app.utils.config import (
    SERVER, DATABASE, DB_USERNAME, DB_PASSWORD, TRUSTED_CONNECTION
)

router = APIRouter()

@router.post("/create_optional_extra")
@exception_handler
async def create_optional_extra(optional_extra: OptionalExtra, token_data: dict = Depends(verify_token)):
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        user_service = UserService(cursor)
        requesting_user = await user_service.get_user_by_id(token_data["user_id"])
        user_service.check_admin(requesting_user)
        validate_required_fields({"optional_extra": optional_extra})
        await optional_extra.validate_optional_extra_values()        
        service = OptionalExtraService(cursor)
        optional_extra = await service.create_optional_extra(optional_extra)
    return JSONResponse(
        content={
            "message": Messages.OPTIONAL_EXTRA_CREATED_SUCCESS,
            "optional_extra": optional_extra.model_dump()
        },
        status_code=HTTPStatus.CREATED
    )

@router.get("/read_optional_extra")
@exception_handler
async def read_optional_extra(
    mode: str,
    extra_id: int = None,
    token_data: dict = Depends(verify_token)
):
    required_fields = {
        "mode": mode,
    }
    if mode == "by_id":
        required_fields["extra_id"] = extra_id
    validate_required_fields(required_fields)
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        service = OptionalExtraService(cursor)

        if mode == "list_all":
            optional_extras = await service.list_all_optional_extras()
        elif mode == "by_id":
            optional_extras = await service.get_optional_extra_by_id(extra_id, format=True)
        else:
            raise ValueError("Invalid mode. Use 'list_all' or 'by_id'.")

    return JSONResponse(
        content={
            "message": Messages.OPTIONAL_EXTRA_READ_SUCCESS,
            "optional_extras": optional_extras
        },
        status_code=HTTPStatus.OK
    )

@router.put("/update_optional_extra")
@exception_handler
async def update_optional_extra(
    updated_optional_extra: OptionalExtra,
    token_data: dict = Depends(verify_token)
):
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        user_service = UserService(cursor)
        requesting_user = await user_service.get_user_by_id(token_data["user_id"])
        user_service.check_admin(requesting_user)
        validate_required_fields({"updated_optional_extra": updated_optional_extra})
        await updated_optional_extra.validate_optional_extra_values()
        service = OptionalExtraService(cursor)
        await service.update_optional_extra(updated_optional_extra)

    return JSONResponse(
        content={
            "message": Messages.OPTIONAL_EXTRA_UPDATED_SUCCESS,
            "optional_extra": updated_optional_extra.model_dump()
        },
        status_code=HTTPStatus.OK
    )

@router.delete("/delete_optional_extra")
@exception_handler
async def delete_optional_extra(extra_id: int, token_data: dict = Depends(verify_token)):
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        user_service = UserService(cursor)
        requesting_user = await user_service.get_user_by_id(token_data["user_id"])
        user_service.check_admin(requesting_user) 
        validate_required_fields({"extra_id": extra_id})               
        service = OptionalExtraService(cursor)
        await service.delete_optional_extra(extra_id)

    return JSONResponse(
        content={
            "message": Messages.OPTIONAL_EXTRA_DELETED_SUCCESS,
            "extra_id": extra_id
        },
        status_code=HTTPStatus.OK
    )
