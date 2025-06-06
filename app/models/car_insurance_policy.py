from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from http import HTTPStatus
import re

from app.utils.response import APIResponse
from app.utils.messages import Messages
from app.utils.field_formatting import capitalise_first

class CarInsurancePolicy(BaseModel):
    ci_policy_id: Optional[int] = Field(None, alias='ci_policy_id')
    user_id: int
    vrn: str
    make: str
    model: str
    policy_number: str
    start_date: str
    end_date: str
    coverage: str

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, user_id: int, vrn: str, make: str, model: str, policy_number: str, start_date: str, end_date: str, coverage: str, ci_policy_id: Optional[int] = None):
        super().__init__(user_id=user_id, vrn=vrn, make=make, model=model, policy_number=policy_number, start_date=start_date, end_date=end_date, coverage=coverage, ci_policy_id=ci_policy_id)
        self.ci_policy_id = ci_policy_id
        self.user_id = user_id
        self.vrn = vrn
        self.make = make
        self.model = model
        self.policy_number = policy_number
        self.start_date = start_date
        self.end_date = end_date
        self.coverage = coverage

    async def validate_car_insurance_policy_values(self):
        validation_errors = []
        error_field = None

        if not error_field:
            if not self.user_id or not self.vrn or not self.make or not self.model or not self.policy_number or not self.start_date or not self.end_date or not self.coverage:
                validation_errors.append("all fields are required.")
                error_field = "required"
        if not error_field:
            if not isinstance(self.policy_number, str) or not self.policy_number.isalnum():
                validation_errors.append("must be alphanumeric.")
                error_field = "policy number"
            elif len(self.policy_number) > 20:
                validation_errors.append("must not be longer than 20 characters.")
                error_field = "policy number"        
        if not error_field:
            if not isinstance(self.vrn, str) or not self.vrn.isalnum():
                validation_errors.append("must be alphanumeric.")
                error_field = "VRN"
            elif len(self.vrn) > 10:
                validation_errors.append("must not be longer than 10 characters.")
                error_field = "VRN"
        if not error_field:
            if not isinstance(self.make, str) or not re.match(r'^[\w\s-]+$', self.make):
                validation_errors.append("must be alphanumeric (spaces and hyphens allowed).")
                error_field = "make"
            elif len(self.make) > 20:
                validation_errors.append("must not be longer than 20 characters.")
                error_field = "make"
        if not error_field:
            if not isinstance(self.model, str) or not re.match(r'^[\w\s-]+$', self.model):
                validation_errors.append("must be alphanumeric (spaces and hyphens allowed).")
                error_field = "model"
            elif len(self.model) > 20:
                validation_errors.append("must not be longer than 20 characters.")
                error_field = "model"
        if not error_field:
            if not isinstance(self.coverage, str) or not self.coverage.replace(" ", "").isalnum():
                validation_errors.append("must be alphanumeric (spaces allowed).")
                error_field = "coverage"
            elif len(self.coverage) > 30:
                validation_errors.append("must not be longer than 30 characters.")
                error_field = "coverage"
        if not error_field:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", self.start_date):
                validation_errors.append("must be in YYYY-MM-DD format.")
                error_field = "start date"
        if not error_field:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", self.end_date):
                validation_errors.append("must be in YYYY-MM-DD format.")
                error_field = "end date"
        if not error_field:
            if self.start_date > self.end_date:
                validation_errors.append("must be before end date.")
                error_field = "start date"

        if validation_errors:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    message=Messages.INVALID_FIELD_VALUE.format(capitalise_first(error_field), validation_errors[0]),
                    data=None
                )
            )
        return True