from http import HTTPStatus

from app.models.optional_extra import OptionalExtra
from app.utils.statements import SelectStatementExecutor, InsertStatementExecutor, DeleteStatementExecutor, UpdateStatementExecutor
from app.utils.debug import Debug
from app.models.car_insurance_policy import CarInsurancePolicy
from app.models.user import User
from app.utils.response import APIResponse
from app.utils.field_formatting import dates_to_string
from app.utils.messages import Messages
from app.services.user_service import UserService
from app.services.optional_extra_service import OptionalExtraService

class CarInsurancePolicyService:
    def __init__(self, cursor, user: User, policy: CarInsurancePolicy, optional_extras: list[OptionalExtra] = None, can_update: bool = False):
        self.cursor = cursor
        self.user = user
        self.user_service = UserService(self.cursor)
        self.policy = policy
        self.can_update = can_update
        self.current_policy = None
        self.optional_extras = optional_extras or []
        self.current_optional_extras = None

    async def verify_optional_extras(self, extra_ids):
        if not extra_ids:
            return set()

        # Fetch all fields for the provided extra IDs
        db_extras = self._fetch_optional_extras_from_db(extra_ids)

        # Validate provided optional extras against database results
        valid_extra_ids = self._validate_provided_extras(db_extras)

        return valid_extra_ids

    def _fetch_optional_extras_from_db(self, extra_ids):
        """
        Fetch optional extras from the database for the given IDs.
        """
        sql = f"SELECT * FROM OptionalExtras WHERE extra_id IN ({','.join(['?'] * len(extra_ids))})"
        Debug.log(f"Fetching optional extras with IDs: {extra_ids}")
        return [OptionalExtra(**row) for row in SelectStatementExecutor(self.cursor).execute_select(sql, tuple(extra_ids))]

    def _validate_provided_extras(self, db_extras):
        """
        Validate the provided optional extras against the database results.
        """
        valid_extra_ids = set()
        for provided_extra in self.optional_extras:
            if any(
                provided_extra.extra_id == db_extra.extra_id and
                provided_extra.name == db_extra.name and
                provided_extra.code == db_extra.code and
                provided_extra.price == db_extra.price
                for db_extra in db_extras
            ):
                valid_extra_ids.add(provided_extra.extra_id)
            else:
                Debug.log(f"Invalid optional extra: {provided_extra.model_dump()}")
        return valid_extra_ids

    async def add_optional_extras(self, policy_id, extra_ids):
        sql_add_extras = """
            INSERT INTO CarInsurancePolicyOptionalExtras (ci_policy_id, extra_id)
            VALUES (?, ?)
        """
        parameters = [(policy_id, extra_id) for extra_id in extra_ids]
        InsertStatementExecutor(self.cursor).execute_insert_many(sql_add_extras, parameters)

    async def remove_optional_extras(self, policy_id, extra_ids):
        sql_remove_extras = """
            DELETE FROM CarInsurancePolicyOptionalExtras
            WHERE ci_policy_id = ? AND extra_id = ?
        """
        parameters = [(policy_id, extra_id) for extra_id in extra_ids]
        DeleteStatementExecutor(self.cursor).execute_delete_many(sql_remove_extras, parameters)

    async def create_car_insurance_policy(self):
        Debug.log(f"Creating car insurance policy with parameters: {self.policy}")
        sql_create_policy = """
            INSERT INTO CarInsurancePolicy (user_id, vrn, make, model, policy_number, start_date, end_date, coverage)
            OUTPUT INSERTED.ci_policy_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        parameters = (
            self.policy.user_id,
            self.policy.vrn,
            self.policy.make,
            self.policy.model,
            self.policy.policy_number,
            self.policy.start_date,
            self.policy.end_date,
            self.policy.coverage
        )
        self.policy.ci_policy_id = InsertStatementExecutor(self.cursor).execute_insert(sql_create_policy, parameters, False)
        
        # Add optional extras if provided
        if self.optional_extras:
            extra_ids = [extra.extra_id for extra in self.optional_extras]
            await self.compare_valid_optional_extras(extra_ids)            
            await self.add_optional_extras(self.policy.ci_policy_id, [extra.extra_id for extra in self.optional_extras])

        # commit the transaction
        self.cursor.commit()
        Debug.log(f"Car insurance policy created with ID: {self.policy.ci_policy_id}")
        return self.policy.ci_policy_id
    
    async def update_car_insurance_policy(self):
        # Check if the policy exists
        await self.check_car_insurance_policy_exists()

        # Check if the user has permission to update the policy
        await self.check_user_update_permissions()

        if self.optional_extras:
            extra_ids = [extra.extra_id for extra in self.optional_extras]
            await self.compare_valid_optional_extras(extra_ids) 

        # Update the car insurance policy
        await self.perform_update()

        # Commit the transaction
        self.cursor.commit()
        Debug.log(f"Car insurance policy updated with ID: {self.policy.ci_policy_id}")

    async def check_car_insurance_policy_exists(self):
        policy = await self.get_car_insurance_policy_by_id(self.policy.ci_policy_id, format=False)
        dates_to_string(policy[0])
        self.current_policy = CarInsurancePolicy(**policy[0])

        # set current optional extras
        sql_get_extras = "SELECT oe.* FROM CarInsurancePolicyOptionalExtras cipoe JOIN OptionalExtras oe ON cipoe.extra_id = oe.extra_id WHERE cipoe.ci_policy_id = ?"
        result = SelectStatementExecutor(self.cursor).execute_select(sql_get_extras, (self.policy.ci_policy_id))
        self.current_optional_extras = [OptionalExtra(**row) for row in result]
        return self.current_policy
    
    async def check_user_update_permissions(self):
        if (
            not self.can_update and self.current_policy.user_id != self.policy.user_id
            ) or (
                not self.user.user_id and self.current_policy.policy_number != self.policy.policy_number
            ):
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.FORBIDDEN,
                    message=Messages.USER_NO_PERMISSION_CHANGE,
                    data=None
                )
            )
        
    async def perform_update(self):
        Debug.log(f"Current policy: {self.current_policy}")
        Debug.log(f"New policy: {self.policy}")
        Debug.log(f"Current optional extras: {self.current_optional_extras}")
        Debug.log(f"New optional extras: {self.optional_extras}")
        policy_changed = self.current_policy != self.policy
        optional_extras_changed = self.current_optional_extras != self.optional_extras

        if (not policy_changed and not optional_extras_changed):
            Debug.log("No changes detected in the car insurance policy")
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    message=Messages.NO_CHANGE,
                    data=None
                )
            )
        if policy_changed:        
            sql_update_policy = """
                UPDATE CarInsurancePolicy
                SET user_id = ?, vrn = ?, make = ?, model = ?, policy_number = ?, start_date = ?, end_date = ?, coverage = ?
                WHERE ci_policy_id = ?
            """
            parameters = (
                self.policy.user_id,
                self.policy.vrn,
                self.policy.make,
                self.policy.model,
                self.policy.policy_number,
                self.policy.start_date,
                self.policy.end_date,
                self.policy.coverage,
                self.policy.ci_policy_id
            )
            Debug.log(f"Updating car insurance policy with parameters: {parameters}")
            UpdateStatementExecutor(self.cursor).execute_update(sql_update_policy, parameters)

        if optional_extras_changed:
            await self.update_optional_extras()

    async def update_optional_extras(self):
        extra_ids = [extra.extra_id for extra in self.optional_extras]        
        await self.compare_valid_optional_extras(extra_ids)

        if self.optional_extras is not None:
            # Get current optional extras for the policy
            current_extras = SelectStatementExecutor(self.cursor).execute_select(
                "SELECT extra_id FROM CarInsurancePolicyOptionalExtras WHERE ci_policy_id = ?", 
                (self.policy.ci_policy_id)
            )
            current_extra_ids = {row["extra_id"] for row in current_extras}
            new_extra_ids = set(extra_ids)

            # Determine extras to add and remove
            extras_to_add = new_extra_ids - current_extra_ids
            extras_to_remove = current_extra_ids - new_extra_ids

            Debug.log(f"Extras to add: {extras_to_add}, Extras to remove: {extras_to_remove}")
            if extras_to_add:
                await self.add_optional_extras(self.policy.ci_policy_id, extras_to_add)

            if extras_to_remove:
                await self.remove_optional_extras(self.policy.ci_policy_id, extras_to_remove)

    async def compare_valid_optional_extras(self, extra_ids):
        if self.optional_extras is not None:
            # Verify all provided optional extra IDs
            valid_extra_ids = await self.verify_optional_extras(extra_ids)

            # Check for invalid IDs
            invalid_ids = set(extra_ids) - valid_extra_ids
            if invalid_ids:
                Debug.log(f"Invalid optional extra ID(s): {invalid_ids}")
                self.cursor.rollback()
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.BAD_REQUEST,
                        message=Messages.OPTIONAL_EXTRAS_NOT_FOUND.format(", ".join(map(str, invalid_ids))),
                        data=None
                    )
                )
            
    async def delete_car_insurance_policy(self):
        # Delete the policy and its optional extras
        # First, delete the optional extras associated with the policy
        # This is done to maintain referential integrity
        # The foreign key constraint should be set to CASCADE delete in the database schema
        # This way, deleting the policy will automatically delete the associated optional extras
        # However, we will do it manually here for clarity
        # Check if the policy has any optional extras before deleting
        # This is optional, but it can help in debugging
        # It also ensures that we are not trying to delete something that doesn't exist
        sql_check_extras = "SELECT oe.* FROM CarInsurancePolicyOptionalExtras cipoe JOIN OptionalExtras oe ON cipoe.extra_id = oe.extra_id WHERE cipoe.ci_policy_id = ?"
        optional_extras = SelectStatementExecutor(self.cursor).execute_select(sql_check_extras, (self.policy.ci_policy_id))
        self.optional_extras = [OptionalExtra(**row) for row in optional_extras]

        if optional_extras:
            await self.remove_optional_extras(self.policy.ci_policy_id, [extra.extra_id for extra in self.optional_extras])

        # Delete the car insurance policy
        sql_delete_policy = "DELETE FROM CarInsurancePolicy WHERE ci_policy_id = ?"
        DeleteStatementExecutor(self.cursor).execute_delete(sql_delete_policy, (self.policy.ci_policy_id))

        Debug.log(f"Car insurance policy deleted with ID: {self.policy.ci_policy_id}")
        return self.policy.ci_policy_id

    async def list_all_car_insurance_policies(self):
        self.user_service.check_admin(self.user)
        policies = SelectStatementExecutor(self.cursor).execute_select("SELECT * FROM CarInsurancePolicy")
        return self.format_car_insurance_policies(policies)

    async def get_car_insurance_policy_by_id(self, policy_id, format: bool = False):
        if not self.user.is_admin and not await self.user_service.check_user_owns_policy(self.user, policy_id):
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.FORBIDDEN,
                    message=Messages.USER_NO_PERMISSION,
                    data=None
                )
            )
        
        result = SelectStatementExecutor(self.cursor).execute_select("SELECT * FROM CarInsurancePolicy WHERE ci_policy_id = ?", (policy_id))
        if not result:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.NOT_FOUND,
                    message=Messages.POLICY_NOT_FOUND,
                    data=None
                )
            )
        if format:
            result = self.format_car_insurance_policies(result)
        return result

    def get_car_insurance_policy_by_user_id(self, user_id):
        if not self.user.is_admin and user_id != self.user.user_id:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.FORBIDDEN,
                    message=Messages.USER_NO_PERMISSION,
                    data=None
                )
            )
        
        policies = SelectStatementExecutor(self.cursor).execute_select("SELECT * FROM CarInsurancePolicy WHERE user_id = ?", (user_id))
        return self.format_car_insurance_policies(policies)

    async def filter_car_insurance_policies(self, field, value):
        self.user_service.check_admin(self.user)
        sql = f"SELECT * FROM CarInsurancePolicy WHERE {field} = ?"
        policies = SelectStatementExecutor(self.cursor).execute_select(sql, (value))
        return self.format_car_insurance_policies(policies)
    
    async def get_policy_extras(self, policies: list[CarInsurancePolicy]):
        policies_with_extras = []
        for policy in policies:
            optional_extras = SelectStatementExecutor(self.cursor).execute_select(
                """
                SELECT oe.extra_id, oe.name, oe.code, oe.price
                FROM CarInsurancePolicyOptionalExtras cipoe
                JOIN OptionalExtras oe ON cipoe.extra_id = oe.extra_id
                WHERE cipoe.ci_policy_id = ?
                """,
                (policy.ci_policy_id)
            )
            extra_service = OptionalExtraService(self.cursor)
            optional_extras = extra_service.format_optional_extras(optional_extras)

            policies_with_extras.append({
                "policy": policy.model_dump(),
                "optional_extras": optional_extras
            })

        return policies_with_extras        

    def format_car_insurance_policies(self, policies):
        formatted_policies = []
        for policy in policies:
            dates_to_string(policy)  # Ensure date fields are formatted
            formatted_policies.append(
                CarInsurancePolicy(
                    ci_policy_id=policy["ci_policy_id"],
                    user_id=policy["user_id"],
                    vrn=policy["vrn"],
                    make=policy["make"],
                    model=policy["model"],
                    policy_number=policy["policy_number"],
                    start_date=policy["start_date"],
                    end_date=policy["end_date"],
                    coverage=policy["coverage"]
                )
            )
        return formatted_policies