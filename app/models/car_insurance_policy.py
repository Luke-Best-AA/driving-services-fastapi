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
        self.vrn = vrn.upper()
        self.make = make
        self.model = model
        self.policy_number = policy_number
        self.start_date = start_date
        self.end_date = end_date
        self.coverage = coverage

    async def validate_car_insurance_policy_values(self):
        self._validate_required_fields()
        self._validate_policy_number()
        self._validate_vrn()
        self._validate_make()
        self._validate_model()
        self._validate_coverage()
        self._validate_dates()
        return True

    def _raise_validation_error(self, field, message):
        raise ValueError(
            APIResponse(
                status=HTTPStatus.BAD_REQUEST,
                message=Messages.INVALID_FIELD_VALUE.format(capitalise_first(field), message),
                data=None
            )
        )

    def _validate_required_fields(self):
        if not self.user_id or not self.vrn or not self.make or not self.model or not self.policy_number or not self.start_date or not self.end_date or not self.coverage:
            self._raise_validation_error("required", "all fields are required.")

    def _validate_policy_number(self):
        if not isinstance(self.policy_number, str) or not self.policy_number.isalnum():
            self._raise_validation_error("policy number", "must be alphanumeric.")
        if len(self.policy_number) > 20:
            self._raise_validation_error("policy number", "must not be longer than 20 characters.")

    def _validate_vrn(self):
        if not isinstance(self.vrn, str) or not re.match(r'^[\w\s]+$', self.vrn):
            self._raise_validation_error("VRN", "must be alphanumeric (spaces allowed).")
        if len(self.vrn) > 10:
            self._raise_validation_error("VRN", "must not be longer than 10 characters.")

    def _validate_make(self):
        if not isinstance(self.make, str) or not re.match(r'^[\w\s-]+$', self.make):
            self._raise_validation_error("make", "must be alphanumeric (spaces and hyphens allowed).")
        if len(self.make) > 20:
            self._raise_validation_error("make", "must not be longer than 20 characters.")

    def _validate_model(self):
        if not isinstance(self.model, str) or not re.match(r'^[\w\s-]+$', self.model):
            self._raise_validation_error("model", "must be alphanumeric (spaces and hyphens allowed).")
        if len(self.model) > 20:
            self._raise_validation_error("model", "must not be longer than 20 characters.")

    def _validate_coverage(self):
        if not isinstance(self.coverage, str) or not self.coverage.replace(" ", "").isalnum():
            self._raise_validation_error("coverage", "must be alphanumeric (spaces allowed).")
        if len(self.coverage) > 30:
            self._raise_validation_error("coverage", "must not be longer than 30 characters.")

    def _validate_dates(self):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", self.start_date):
            self._raise_validation_error("start date", "must be in YYYY-MM-DD format.")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", self.end_date):
            self._raise_validation_error("end date", "must be in YYYY-MM-DD format.")
        if self.start_date > self.end_date:
            self._raise_validation_error("start date", "must be before end date.")