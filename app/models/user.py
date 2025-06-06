from pydantic import BaseModel, Field, ConfigDict

from typing import Optional
from http import HTTPStatus

from app.utils.debug import Debug  # Import the Debug class
from app.utils.messages import Messages  # Import the Messages class
from app.utils.response import APIResponse  # Import the APIResponse class

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

        # Track which field caused the first error
        error_field = None

        if not error_field:
            self._validate_username(validation_errors)
            if validation_errors:
                error_field = "username"
        if not error_field and self.password != "":
            self._validate_password(validation_errors)
            if validation_errors:
                error_field = "password"
        if not error_field:
            self._validate_email(validation_errors)
            if validation_errors:
                error_field = "email"
        if not error_field:
            self._validate_is_admin(validation_errors)
            if validation_errors:
                error_field = "is_admin"

        if validation_errors:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    message=Messages.INVALID_FIELD_VALUE.format(error_field, validation_errors[0]),
                    data=None
                )
            )           
        return True

    def _validate_username(self, validation_errors):
        if self.username is not None:
            if len(self.username) > 20:
                validation_errors.append("must not be longer than 20 characters")
            elif not self.username.isalnum() or not self.username[0].isalpha() or len(self.username) < 4:
                validation_errors.append("must be alphanumeric, start with a letter, and be at least 4 characters long")

    def _validate_password(self, validation_errors):
        if self.password is not None:
            if self.password == "":
                return
            if not re.fullmatch(r"[a-fA-F0-9]{32}", self.password):
                validation_errors.append("must be a 32-character hexadecimal string")

    def _validate_email(self, validation_errors):
        if self.email is not None:
            if len(self.email) > 32:
                validation_errors.append("must not be longer than 32 characters")
            elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", self.email):
                validation_errors.append("must be in format: name@example.com")

    def _validate_is_admin(self, validation_errors):
        if self.is_admin is not None:
            Debug.log("Validating is_admin value")
            if not isinstance(self.is_admin, (bool, int)) or self.is_admin not in [True, False, 1, 0]:
                validation_errors.append("must be a boolean value (True/False or 1/0)")
            else:
                self.is_admin = bool(self.is_admin)