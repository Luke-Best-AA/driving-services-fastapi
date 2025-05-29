from fastapi import HTTPException
from http import HTTPStatus

from ..statements import InsertStatementExecutor, UpdateStatementExecutor, DeleteStatementExecutor, SelectStatementExecutor
from ..response import APIResponse
from ..optional_extra import OptionalExtra
from ..messages import Messages

class OptionalExtraService:
    def __init__(self, cursor):
        """
        Initializes the OptionalExtraService with a database cursor.

        :param cursor: A database cursor object for executing queries.
        """
        self.cursor = cursor

    async def create_optional_extra(self, optional_extra: OptionalExtra):
        """
        Creates a new optional extra in the database.

        :param optional_extra: The OptionalExtra object containing the details to insert.
        :return: The created optional extra with its ID.
        """
        executor = InsertStatementExecutor(self.cursor)
        sql = """
            INSERT INTO OptionalExtras (name, code, price)
            OUTPUT INSERTED.extra_id
            VALUES (?, ?, ?)
        """
        optional_extra.extra_id = executor.execute_insert(sql, (optional_extra.name, optional_extra.code, optional_extra.price))
        return optional_extra

    async def update_optional_extra(self, updated_optional_extra: OptionalExtra):
        """
        Updates an existing optional extra in the database.

        :param updated_optional_extra: The updated OptionalExtra object.
        """
        # Check if the optional extra exists
        existing_optional_extra = await self.get_optional_extra_by_id(updated_optional_extra.extra_id)

        if not existing_optional_extra:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.NOT_FOUND,
                    message=Messages.OPTIONAL_EXTRA_NOT_FOUND,
                    data=None
                )
            )

        # Check if there are changes
        existing_optional_extra = OptionalExtra(**existing_optional_extra[0])
        if existing_optional_extra == updated_optional_extra:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    message=Messages.NO_CHANGE,
                    data=None
                )
            )

        # Update the optional extra
        executor = UpdateStatementExecutor(self.cursor)
        sql = """
            UPDATE OptionalExtras
            SET name = ?, code = ?, price = ?
            WHERE extra_id = ?
        """
        executor.execute_update(sql, (updated_optional_extra.name, updated_optional_extra.code, updated_optional_extra.price, updated_optional_extra.extra_id))

    async def delete_optional_extra(self, extra_id: int):
        """
        Deletes an optional extra from the database.

        :param extra_id: The ID of the optional extra to delete.
        """
        # Check if the optional extra exists
        optional_extra = await self.get_optional_extra_by_id(extra_id)

        if not optional_extra:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.NOT_FOUND,
                    message=Messages.OPTIONAL_EXTRA_NOT_FOUND,
                    data=None
                )
            )

        # Check for related records in CarInsurancePolicyOptionalExtras
        select_executor = SelectStatementExecutor(self.cursor)
        related_records = select_executor.execute_select(
            "SELECT * FROM CarInsurancePolicyOptionalExtras WHERE extra_id = ?", (extra_id,)
        )
        if related_records:
            # Delete related joining records first
            delete_join_executor = DeleteStatementExecutor(self.cursor)
            delete_join_executor.execute_delete(
                "DELETE FROM CarInsurancePolicyOptionalExtras WHERE extra_id = ?", (extra_id,)
            )

        # Delete the optional extra
        executor = DeleteStatementExecutor(self.cursor)
        sql = "DELETE FROM OptionalExtras WHERE extra_id = ?"
        executor.execute_delete(sql, (extra_id))

    async def list_all_optional_extras(self):
        optional_extras = SelectStatementExecutor(self.cursor).execute_select("SELECT * FROM OptionalExtras")
        self.error_not_found(optional_extras)
        return self.format_optional_extras(optional_extras)

    async def get_optional_extra_by_id(self, extra_id, format: bool = False):
        optional_extra = SelectStatementExecutor(self.cursor).execute_select("SELECT * FROM OptionalExtras WHERE extra_id = ?", (extra_id))
        
        self.error_not_found(optional_extra)
        if format:
            optional_extra = self.format_optional_extras(optional_extra)

        return optional_extra
    
    def error_not_found(self, optional_extra):
        if not optional_extra:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.NOT_FOUND,
                    message=Messages.OPTIONAL_EXTRA_NOT_FOUND,
                    data=None
                )
            )

    def format_optional_extras(self, optional_extras):
        return [
            OptionalExtra(
                extra_id=extra["extra_id"],
                name=extra["name"],
                code=extra["code"],
                price=float(extra["price"])
            ).model_dump()
            for extra in optional_extras
        ]