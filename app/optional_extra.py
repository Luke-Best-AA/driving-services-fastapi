from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from http import HTTPStatus
from .response import APIResponse
from .messages import Messages

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

            self._validate_required_fields(validation_errors)
            self._validate_price(validation_errors)
            self._validate_name(validation_errors)
            self._validate_code(validation_errors)

            if validation_errors:
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.BAD_REQUEST,
                        message=Messages.INVALID_FIELD_VALUE.format(", ".join(validation_errors), "optional extra"),
                        data=None
                    )
                )
            return True

    def _validate_required_fields(self, validation_errors):
        if not self.name or not self.code or not self.price:
            validation_errors.append("All fields are required.")

    def _validate_price(self, validation_errors):
        if not isinstance(self.price, (int, float)):
            validation_errors.append("Price must be a number.")
        elif self.price <= 0:
            validation_errors.append("Price must be a positive number.")

    def _validate_name(self, validation_errors):
        if not all(c.isalnum() or c.isspace() for c in self.name):
            validation_errors.append("Name must be alphanumeric and can include spaces.")

    def _validate_code(self, validation_errors):
        if not self.code.isalnum() or len(self.code) >= 10:
            validation_errors.append("Code must be alphanumeric and less than 10 characters.")