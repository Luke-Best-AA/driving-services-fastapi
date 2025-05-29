from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import RequestValidationError

from starlette.requests import Request

from .user import User
from .optional_extra import OptionalExtra
from .car_insurance_policy import CarInsurancePolicy
from .response import APIResponse
from .db_connect import DBConnect
from .debug import Debug

from .config import (
    ACCESS_TOKEN_EXPIRY_MINS, REFRESH_TOKEN_EXPIRY_HOURS,
    SERVER, DATABASE, DB_USERNAME, DB_PASSWORD, TRUSTED_CONNECTION
)
from .messages import Messages

from .services.car_insurance_policy_service import CarInsurancePolicyService
from .services.optional_extra_service import OptionalExtraService
from .services.user_service import UserService

from dotenv import load_dotenv
import os
import jwt
import datetime
from http import HTTPStatus
from functools import wraps

app = FastAPI()

# Mount static files
app.mount("/app/static", StaticFiles(directory="app/static"), name="static")

Debug.enabled = True

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Load environment variables from .env file
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")  # Load SECRET_KEY from .env

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in the environment variables")

ALGORITHM = "HS256"  # JWT signing algorithm

# OAuth2 setup
class CustomOAuth2PasswordBearer(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str:
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail=Messages.AUTHORIZATION_HEADER_MISSING,
            )
        return await super().__call__(request)

oauth2_scheme = CustomOAuth2PasswordBearer(tokenUrl="token")

def validate_required_fields(fields: dict):
    """
    Validates that required fields are provided.
    :param fields: A dictionary where keys are field names and values are the field values.
    :raises HTTPException: If any field is missing or invalid.
    """
    for field_name, value in fields.items():
        if value is None:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    message=Messages.FIELD_REQUIRED.format(field_name),
                    data=None
                )
            )

def exception_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            if isinstance(e.args[0], APIResponse):
                api_response = e.args[0]
                raise HTTPException(
                    status_code=api_response.status,
                    detail=api_response.message
                )
            else:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=str(e)
                )
        except Exception as e:
            Debug.log(f"Error: {str(e)}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=Messages.DB_ERROR
            )
    return wrapper

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTPStatus.BAD_REQUEST,
        content={
            "message": Messages.INVALID_REQUEST_DATA,
            "errors": exc.errors(),
        },
    )

@app.get("/healthcheck")
async def healthcheck():
    return JSONResponse(
        content={
            "message": Messages.API_IS_RUNNNG
        },
        status_code=HTTPStatus.OK
    )

@app.post("/token")
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

@app.post("/refresh_token")
async def refresh_token(refresh_token: str = Depends(oauth2_scheme)):
    try:
        # Decode and validate the refresh token
        decoded_token = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded_token["user_id"]
        username = decoded_token["username"]

        # Generate a new access token
        access_token_data = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)  # Access token expires in 15 minutes
        }
        access_token = jwt.encode(access_token_data, SECRET_KEY, algorithm=ALGORITHM)

        # Generate a new refresh token (rotated)
        refresh_token_data = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)  # Refresh token expires in 7 days
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
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
        },
        status_code=HTTPStatus.OK
    )

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        Debug.log(f"Token verified for user_id: {decoded_token['user_id']}")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=Messages.TOKEN_HAS_EXPIRED
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=Messages.INVALID_TOKEN
        )
    except Exception as e:
        Debug.log(f"Error verifying token: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=Messages.TOKEN_VERIFICATION_FAILED
        )
    return decoded_token

@app.post("/verify_authentication")
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

@app.post("/create_user")
@exception_handler
async def create_user(user: User, token_data: dict = Depends(verify_token)):
    Debug.log(f"Getting user details using user_id: {token_data['user_id']}")    
    # Use the service to create the user
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

@app.get("/read_user")
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

@app.put("/update_user")
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

@app.delete("/delete_user")
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

@app.post("/create_optional_extra")
@exception_handler
async def create_optional_extra(optional_extra: OptionalExtra, token_data: dict = Depends(verify_token)):
    # Use the service to create the optional extra
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

@app.get("/read_optional_extra")
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

@app.put("/update_optional_extra")
@exception_handler
async def update_optional_extra(
    updated_optional_extra: OptionalExtra,
    token_data: dict = Depends(verify_token)
):
    # Use the service to update the optional extra
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

@app.delete("/delete_optional_extra")
@exception_handler
async def delete_optional_extra(extra_id: int, token_data: dict = Depends(verify_token)):
    # Use the service to delete the optional extra
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

@app.post("/create_car_insurance_policy")
@exception_handler
async def create_car_insurance_policy(
    policy: CarInsurancePolicy,
    optional_extras: list[OptionalExtra] = None,
    token_data: dict = Depends(verify_token)
):
    # Logic to create a new car insurance policy in the database
    with DBConnect(SERVER, DATABASE, TRUSTED_CONNECTION, DB_USERNAME, DB_PASSWORD) as db:
        cursor = db.connection.cursor()
        user_service = UserService(cursor)
        requesting_user = await user_service.get_user_by_id(token_data["user_id"])
        # Ensure non-admin users can only create policies for their own user_id
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

@app.get("/read_car_insurance_policy")
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

        # Include optional extras for each policy
        policies_with_extras = await service.get_policy_extras(policies)

    return JSONResponse(
        content={
            "message": Messages.POLICY_READ_SUCCESS,
            "policies": policies_with_extras
        },
        status_code=HTTPStatus.OK
    )

@app.put("/update_car_insurance_policy")
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

        # Update policy details
        await service.update_car_insurance_policy()

    return JSONResponse(
        content={
            "message": Messages.POLICY_UPDATED_SUCCESS,
            "policy": updated_policy.model_dump(),
            "optional_extras": [extra.model_dump() for extra in optional_extras] if optional_extras else None
        },
        status_code=HTTPStatus.OK
    )

@app.delete("/delete_car_insurance_policy")
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

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"request": request})

@app.get("/admin_dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse(request, "admin-dashboard.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse(request, "profile.html", {"request": request})