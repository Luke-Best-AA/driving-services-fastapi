from fastapi import HTTPException, Depends
from http import HTTPStatus
from functools import wraps
import jwt
import os

from app.utils.response import APIResponse
from .debug import Debug
from app.utils.messages import Messages
from app.utils.auth import oauth2_scheme
from app.utils.config import ALGORITHM
from .messages import Messages
from app.utils.debug import Debug

# Utility: Validate required fields

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

# Utility: Exception handler decorator

def exception_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            # Ensure e.args exists and is not empty
            if hasattr(e, "args") and e.args and isinstance(e.args[0], APIResponse):
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

# Utility: Verify token

def verify_token(token: str = Depends(oauth2_scheme)):
    SECRET_KEY = os.getenv("SECRET_KEY")
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
