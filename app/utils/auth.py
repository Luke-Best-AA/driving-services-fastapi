from fastapi.security import OAuth2PasswordBearer
from fastapi import Request, HTTPException
from http import HTTPStatus
from .messages import Messages

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
