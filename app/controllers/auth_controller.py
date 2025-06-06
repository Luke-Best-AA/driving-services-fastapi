from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from http import HTTPStatus
import datetime
import jwt
import os

from app.utils.response import APIResponse
from app.utils.debug import Debug
from app.utils.messages import Messages
from app.utils.db_connect import DBConnect
from app.services.user_service import UserService
from app.utils.common import exception_handler, verify_token
from app.utils.config import (
    ACCESS_TOKEN_EXPIRY_MINS, REFRESH_TOKEN_EXPIRY_HOURS,
    SERVER, DATABASE, DB_USERNAME, DB_PASSWORD, TRUSTED_CONNECTION
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

@router.post("/token")
@exception_handler
async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
            cursor = db.connection.cursor()
            service = UserService(cursor)
            Debug.log(f"Authenticating user: {form_data.username}")
            user = await service.authenticate_user(form_data.username, form_data.password)

        # Generate access token
        access_token_data = {
            "user_id": user.user_id,
            "username": user.username,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINS)
        }
        access_token = jwt.encode(access_token_data, SECRET_KEY, algorithm=ALGORITHM)

        # Generate refresh token
        refresh_token_data = {
            "user_id": user.user_id,
            "username": user.username,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=REFRESH_TOKEN_EXPIRY_HOURS)
        }
        refresh_token = jwt.encode(refresh_token_data, SECRET_KEY, algorithm=ALGORITHM)

    except ValueError:
        raise ValueError(
            APIResponse(
                status=HTTPStatus.UNAUTHORIZED,
                message=Messages.USER_INVALID_CREDENTIALS,
                data=None
            )
        )
    
    return JSONResponse(
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
        },
        status_code=HTTPStatus.OK
    )

@router.post("/refresh_token")
async def refresh_token(refresh_token: str = Depends(oauth2_scheme)):
    try:
        decoded_token = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded_token["user_id"]
        username = decoded_token["username"]

        access_token_data = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINS)
        }
        access_token = jwt.encode(access_token_data, SECRET_KEY, algorithm=ALGORITHM)

        refresh_token_data = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=REFRESH_TOKEN_EXPIRY_HOURS)
        }
        new_refresh_token = jwt.encode(refresh_token_data, SECRET_KEY, algorithm=ALGORITHM)

        with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
            cursor = db.connection.cursor()
            service = UserService(cursor)
            Debug.log(f"Refreshing token for user_id: {user_id}")
            user = await service.get_user_by_id(user_id)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=Messages.REFRESH_TOKEN_EXPIRED
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=Messages.INVALID_REFRESH_TOKEN
        )
    
    return JSONResponse(
        content={
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
        },
        status_code=HTTPStatus.OK
    )

@router.post("/verify_authentication")
@exception_handler
async def verify_authentication(token_data: dict = Depends(verify_token)):
    response_content = {
        "user_id": token_data["user_id"],
        "message": Messages.TOKEN_VERIFICATION_SUCCESS
    }
    if "username" in token_data:
        response_content["username"] = token_data["username"]
    return JSONResponse(
        content=response_content,
        status_code=HTTPStatus.OK
    )