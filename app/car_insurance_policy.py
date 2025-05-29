from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from http import HTTPStatus
import re

from .response import APIResponse
from .messages import Messages

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
        if not self.user_id or not self.vrn or not self.make or not self.model or not self.policy_number or not self.start_date or not self.end_date or not self.coverage:
            validation_errors.append("All fields are required.")
        # for vrn, make, model, policy_number, coverage
        if not isinstance(self.vrn, str) or not self.vrn.isalnum() or len(self.vrn) >= 10:
            validation_errors.append("VRN must be alphanumeric and less than 10 characters.")

        if not isinstance(self.make, str) or not re.match(r'^[\w\s-]+$', self.make) or len(self.make) >= 20:
            validation_errors.append("Make must be alphanumeric (spaces and hyphens allowed) and less than 20 characters.")

        if not isinstance(self.model, str) or not re.match(r'^[\w\s-]+$', self.model) or len(self.model) >= 20:
            validation_errors.append("Model must be alphanumeric (spaces and hyphens allowed) and less than 20 characters.")

        if not isinstance(self.policy_number, str) or not self.policy_number.isalnum() or len(self.policy_number) >= 20:
            validation_errors.append("Policy number must be alphanumeric and less than 20 characters.")

        if not isinstance(self.coverage, str) or not self.coverage.replace(" ", "").isalnum() or len(self.coverage) >= 20:
            validation_errors.append("Coverage must be alphanumeric (spaces allowed) and less than 20 characters.")

        # Validate date format (YYYY-MM-DD)
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", self.start_date):
            validation_errors.append("Start date must be in YYYY-MM-DD format.")

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", self.end_date):
            validation_errors.append("End date must be in YYYY-MM-DD format.")

        # Validate date order
        if self.start_date > self.end_date:
            validation_errors.append("Start date must be before end date.")
            
        if validation_errors:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    message=Messages.INVALID_FIELD_VALUE.format(", ".join(validation_errors), "car insurance policy"),
                    data=None
                )
            )
        return True