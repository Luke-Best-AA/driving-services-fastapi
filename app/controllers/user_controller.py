from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from http import HTTPStatus

from app.models.user import User
from app.utils.response import APIResponse
from app.utils.debug import Debug
from app.utils.messages import Messages
from app.utils.db_connect import DBConnect
from app.services.user_service import UserService
from app.utils.common import validate_required_fields, exception_handler, verify_token
from app.utils.config import (
    SERVER, DATABASE, DB_USERNAME, DB_PASSWORD, TRUSTED_CONNECTION
)

router = APIRouter()

class UpdateUserPasswordPayload(BaseModel):
    user_id: int
    existing_password: str
    new_password: str

@router.post("/create_user")
@exception_handler
async def create_user(user: User, token_data: dict = Depends(verify_token)):
    Debug.log(f"Getting user details using user_id: {token_data['user_id']}")    
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        service = UserService(cursor)
        requesting_user = await service.get_user_by_id(token_data["user_id"])
        service.check_admin(requesting_user)
        validate_required_fields({"user": user})
        user.validate_user_values()        
        user = await service.create_user(user)
    return JSONResponse(
        content={
            "message": Messages.USER_CREATED_SUCCESS,
            "user": user.model_dump()
        },
        status_code=HTTPStatus.CREATED
    )

@router.get("/read_user")
@exception_handler
async def read_user(
    mode: str,
    field: str = None,
    value: str = None,
    user_id: int = None,
    token_data: dict = Depends(verify_token)
):
    required_fields = {
        "mode": mode,
    }
    if mode == "filter":
        required_fields["field"] = field
        required_fields["value"] = value
    elif mode == "by_id":
        required_fields["user_id"] = user_id
    validate_required_fields(required_fields)
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        service = UserService(cursor)
        requesting_user = await service.get_user_by_id(token_data["user_id"])

        if mode == "list_all":
            users = await service.list_all_users(requesting_user)
        elif mode == "filter":
            users = await service.filter_users(requesting_user, field, value)
        elif mode == "by_id":
            users = await service.get_user_by_id(user_id, requesting_user, format=True)
        elif mode == "myself":
            users = await service.get_user_by_id(requesting_user.user_id, requesting_user, format=True)
        else:
            raise ValueError("Invalid mode. Use 'list_all', 'filter', 'by_id' or 'myself'.")
    return JSONResponse(
        content={
            "message": Messages.USER_READ_SUCCESS,
            "users": users
        },
        status_code=HTTPStatus.OK
    )

@router.put("/update_user")
@exception_handler
async def update_user(updated_user: User, token_data: dict = Depends(verify_token)):
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        service = UserService(cursor)
        requesting_user = await service.get_user_by_id(token_data["user_id"])
        service.check_update_permissions(requesting_user, updated_user.user_id)
        validate_required_fields({"updated_user": updated_user})
        updated_user.validate_user_values()
        updated_user.password = None        
        await service.update_user(updated_user)
    return JSONResponse(
        content={
            "message": Messages.USER_UPDATED_SUCCESS,
            "user": updated_user.model_dump()
        },
        status_code=HTTPStatus.OK
    )

@router.patch("/update_user_password")
@exception_handler
async def update_user_password(
    payload: UpdateUserPasswordPayload,
    token_data: dict = Depends(verify_token)
):
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        service = UserService(cursor)
        requesting_user = await service.get_user_by_id(token_data["user_id"])
        service.check_update_permissions(requesting_user, payload.user_id)
        validate_required_fields({
            "user_id": payload.user_id,
            "existing_password": payload.existing_password,
            "new_password": payload.new_password
        })

        user = await service.get_user_by_id(payload.user_id, requesting_user, password=True)
        user_new_password = User(
            user_id=user.user_id,
            username=user.username,
            password=payload.new_password,
            email=user.email,
            is_admin=user.is_admin
        )
        user_new_password.validate_user_values()

        if payload.existing_password == "":
            if not requesting_user.is_admin:
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.FORBIDDEN,
                        message=Messages.USER_NO_PERMISSION,
                        data=None
                    )
                )
        else:
            if not service.verify_password(payload.existing_password, user.password):
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.BAD_REQUEST,
                        message=Messages.USER_INVALID_CREDENTIALS,
                        data=None
                    )
                )
            if payload.new_password == user.password:
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.BAD_REQUEST,
                        message=Messages.NO_CHANGE,
                        data=None
                    )
                )

        await service.update_user_password(payload.user_id, payload.new_password)
    return JSONResponse(
        content={
            "message": Messages.USER_PASSWORD_UPDATED_SUCCESS,
            "user_id": payload.user_id
        },
        status_code=HTTPStatus.OK
    )

@router.delete("/delete_user")
@exception_handler
async def delete_user(user_id: int, token_data: dict = Depends(verify_token)):
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        service = UserService(cursor)
        requesting_user = await service.get_user_by_id(token_data["user_id"])
        service.check_admin(requesting_user)
        validate_required_fields({"user_id": user_id})        
        await service.delete_user(user_id)
    return JSONResponse(
        content={
            "message": Messages.USER_DELETED_SUCCESS,
            "user_id": user_id
        },
        status_code=HTTPStatus.OK
    )

@router.post("/register_user")
@exception_handler
async def register_user(user: User):
    Debug.log(f"Registering new user: {user.username}")
    validate_required_fields({"user": user})
    user.validate_user_values()
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        service = UserService(cursor)
        user = await service.create_user(user)
    return JSONResponse(
        content={
            "message": Messages.USER_CREATED_SUCCESS,
            "user": user.model_dump()
        },
        status_code=HTTPStatus.CREATED
    )
