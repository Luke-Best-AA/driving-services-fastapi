from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from http import HTTPStatus

from app.utils.response import APIResponse
from app.utils.messages import Messages

class OptionalExtra(BaseModel):
    extra_id: Optional[int] = Field(None, alias='extra_id')
    name: str
    code: str
    price: float

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, name: str, code: str, price: float, extra_id: Optional[int] = None):
        super().__init__(name=name, code=code, price=price, extra_id=extra_id)
        self.extra_id = extra_id
        self.name = name
        self.code = code
        self.price = price

    async def validate_optional_extra_values(self):
        validation_errors = []
        error_field = None

        if not error_field:
            self._validate_required_fields(validation_errors)
            if validation_errors:
                error_field = "required"
        if not error_field:
            self._validate_price(validation_errors)
            if validation_errors:
                error_field = "price"
        if not error_field:
            self._validate_name(validation_errors)
            if validation_errors:
                error_field = "name"
        if not error_field:
            self._validate_code(validation_errors)
            if validation_errors:
                error_field = "code"

        if validation_errors:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    message=Messages.INVALID_FIELD_VALUE.format(error_field, validation_errors[0]),
                    data=None
                )
            )
        return True

    def _validate_required_fields(self, validation_errors):
        if not self.name or not self.code or not self.price:
            validation_errors.append("all fields are required.")

    def _validate_price(self, validation_errors):
        if not isinstance(self.price, (int, float)):
            validation_errors.append("must be a number.")
        elif self.price <= 0:
            validation_errors.append("must be a positive number.")

    def _validate_name(self, validation_errors):
        if len(self.name) > 32:
            validation_errors.append("must not be longer than 32 characters.")
        elif not all(c.isalnum() or c.isspace() for c in self.name):
            validation_errors.append("must be alphanumeric and can include spaces.")

    def _validate_code(self, validation_errors):
        if len(self.code) > 10:
            validation_errors.append("must not be longer than 10 characters.")
        elif not self.code.isalnum():
            validation_errors.append("must be alphanumeric.")