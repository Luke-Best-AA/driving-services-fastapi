from pydantic import BaseModel, Field, ConfigDict

from typing import Optional
from .debug import Debug  # Import the Debug class
from .messages import Messages  # Import the Messages class
from http import HTTPStatus
from .response import APIResponse  # Import the APIResponse class

import re

class User(BaseModel):
    user_id: Optional[int] = Field(default=0, description="User ID can be 0 or not passed")
    username: str
    password: Optional[str] = Field(default="", description="Password can be empty")
    email: str
    is_admin: bool

    model_config = ConfigDict(from_attributes=True) 

    def __init__(self, **data):
        super().__init__(**data)
    
    def validate_user_values(self):
        Debug.log("Validating user values")
        validation_errors = []

        self._validate_username(validation_errors)
        self._validate_password(validation_errors)
        self._validate_email(validation_errors)
        self._validate_is_admin(validation_errors)

        if validation_errors:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    message=Messages.INVALID_FIELD_VALUE.format(", ".join(validation_errors), "user"),
                    data=None
                )
            )           
        return True

    def _validate_username(self, validation_errors):
        if self.username is not None:
            if not self.username.isalnum() or not self.username[0].isalpha() or len(self.username) < 5:
                validation_errors.append("username must be alphanumeric, start with a letter, and be at least 5 characters long")

    def _validate_password(self, validation_errors):
        if self.password is not None:
            if self.password == "":
                return
            if not re.fullmatch(r"[a-fA-F0-9]{32}", self.password):
                validation_errors.append("password must be a 32-character hexadecimal string")

    def _validate_email(self, validation_errors):
        if self.email is not None:
            if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", self.email):
                validation_errors.append("email must be a valid email address")

    def _validate_is_admin(self, validation_errors):
        if self.is_admin is not None:
            Debug.log("Validating is_admin value")
            if not isinstance(self.is_admin, (bool, int)) or self.is_admin not in [True, False, 1, 0]:
                validation_errors.append("is_admin must be a boolean value (True/False or 1/0)")
            else:
                self.is_admin = bool(self.is_admin)