from .debug import Debug
from .response import APIResponse
from app.utils.messages import Messages
from http import HTTPStatus

from .error_constants import TYPE_CONVERSION_ERROR, UNIQUE_KEY_CONSTRAINT

class SelectStatementExecutor:
    def __init__(self, cursor):
        """
        Initializes the SelectStatementExecutor with an existing database cursor.

        :param cursor: A database cursor object for executing queries.
        """
        self.cursor = cursor

    def execute_select(self, query, params=None):
        """
        Executes a SELECT statement and returns the results.

        :param query: The SQL SELECT query as a string.
        :param params: Optional dictionary or tuple of parameters for the query.
        :return: List of rows as dictionaries.
        """
        try:
            Debug.log(f"Executing SQL: {query} with parameters: {params}")
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            result = self.cursor.fetchall()
        
        except Exception as e:
            Debug.log(f"Database error during select: {str(e)}")
            self.cursor.connection.rollback()
            if TYPE_CONVERSION_ERROR in str(e):
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.BAD_REQUEST,
                        message=Messages.INVALID_TYPE,
                        data=None
                    )
                )
            elif UNIQUE_KEY_CONSTRAINT in str(e):
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.CONFLICT,
                        message=Messages.DUPLICATION_ERROR,
                        data=None
                    )
                )
            else:
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.INTERNAL_SERVER_ERROR,
                        message=Messages.DB_ERROR,
                        data=None
                    )
                )
        
        return [dict(zip([column[0] for column in self.cursor.description], row)) for row in result]
        
class InsertStatementExecutor:
    def __init__(self, cursor):
        """
        Initializes the InsertStatementExecutor with an existing database cursor.

        :param cursor: A database cursor object for executing queries.
        """
        self.cursor = cursor

    def execute_insert(self, query, params=None, commit=True):
        """
        Executes an INSERT statement.

        :param query: The SQL INSERT query as a string.
        :param params: Optional dictionary or tuple of parameters for the query.
        """
        try:
            Debug.log(f"Executing SQL: {query} with parameters: {params}")
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            record_id = self.cursor.fetchone()[0]
            Debug.log(f"Inserted record with ID: {record_id}")

            if commit:
                self.cursor.connection.commit()
        except Exception as e:
            self.cursor.connection.rollback()
            Debug.log(f"Database error during insert: {str(e)}")
            if UNIQUE_KEY_CONSTRAINT in str(e):
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.CONFLICT,
                        message=Messages.DUPLICATION_ERROR,
                        data=None
                    )
                )
            elif TYPE_CONVERSION_ERROR in str(e):
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.BAD_REQUEST,
                        message=Messages.INVALID_TYPE,
                        data=None
                    )
                )
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    message=Messages.DB_ERROR,
                    data=None
                )
            )
            
        return record_id
        
    def execute_insert_many(self, query, params=None):
        """
        Executes an INSERT statement for multiple records.

        :param query: The SQL INSERT query as a string.
        :param params: List of tuples or dictionaries of parameters for the query.
        """
        try:
            Debug.log(f"Executing SQL: {query} with parameters: {params}")
            if params:
                self.cursor.executemany(query, params)
            else:
                self.cursor.execute(query)

            inserted_count = self.cursor.rowcount if self.cursor.rowcount != -1 else len(params)
            Debug.log(f"Inserted {inserted_count} record(s)")
        except Exception as e:
            self.cursor.connection.rollback()
            Debug.log(f"Database error during insert many: {str(e)}")
            if UNIQUE_KEY_CONSTRAINT in str(e):
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.CONFLICT,
                        message=Messages.DUPLICATION_ERROR,
                        data=None
                    )
                )
            elif TYPE_CONVERSION_ERROR in str(e):
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.BAD_REQUEST,
                        message=Messages.INVALID_TYPE,
                        data=None
                    )
                )
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    message=Messages.DB_ERROR,
                    data=None
                )
            )
        
class UpdateStatementExecutor:
    def __init__(self, cursor):
        """
        Initializes the UpdateStatementExecutor with an existing database cursor.

        :param cursor: A database cursor object for executing queries.
        """
        self.cursor = cursor

    def execute_update(self, query, params=None, commit=True):
        """
        Executes an UPDATE statement.

        :param query: The SQL UPDATE query as a string.
        :param params: Optional dictionary or tuple of parameters for the query.
        """
        try:
            Debug.log(f"Executing SQL: {query} with parameters: {params}")
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            if self.cursor.rowcount == 0:
                raise ValueError(Messages.RECORD_NOT_FOUND)
            if commit:
                self.cursor.connection.commit()
            Debug.log(f"Updated {self.cursor.rowcount} record(s)")

        except Exception as e:
            self.cursor.connection.rollback()
            Debug.log(f"Database error during update: {str(e)}")
            if UNIQUE_KEY_CONSTRAINT in str(e):
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.CONFLICT,
                        message=Messages.DUPLICATION_ERROR,
                        data=None
                    )
                )
            elif TYPE_CONVERSION_ERROR in str(e):
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.BAD_REQUEST,
                        message=Messages.INVALID_TYPE,
                        data=None
                    )
                )
            elif Messages.RECORD_NOT_FOUND in str(e):
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.NOT_FOUND,
                        message=Messages.RECORD_NOT_FOUND,
                        data=None
                    )
                )
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    message=Messages.DB_ERROR,
                    data=None
                )
            )
        
class DeleteStatementExecutor:
    def __init__(self, cursor):
        """
        Initializes the DeleteStatementExecutor with an existing database cursor.

        :param cursor: A database cursor object for executing queries.
        """
        self.cursor = cursor

    def execute_delete(self, query, params=None, commit=True):
        """
        Executes a DELETE statement.

        :param query: The SQL DELETE query as a string.
        :param params: Optional dictionary or tuple of parameters for the query.
        """
        try:
            Debug.log(f"Executing SQL: {query} with parameters: {params}")
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if self.cursor.rowcount == 0:
                raise ValueError(Messages.RECORD_NOT_FOUND)
            
            if commit:
                self.cursor.connection.commit()
            Debug.log(f"Deleted {self.cursor.rowcount} record(s)")

        except Exception as e:
            self.cursor.connection.rollback()
            Debug.log(f"Database error during delete: {str(e)}")

            if Messages.RECORD_NOT_FOUND in str(e):
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.NOT_FOUND,
                        message=Messages.RECORD_NOT_FOUND,
                        data=None
                    )
                )
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    message=Messages.DB_ERROR,
                    data=None
                )
            )
        
    def execute_delete_many(self, query, params=None, commit=True):
        """
        Executes a DELETE statement for multiple records.

        :param query: The SQL DELETE query as a string.
        :param params: List of tuples or dictionaries of parameters for the query.
        """
        try:
            Debug.log(f"Executing SQL: {query} with parameters: {params}")
            if params:
                self.cursor.executemany(query, params)
            else:
                self.cursor.execute(query)

            if commit:
                self.cursor.connection.commit()

            Debug.log(f"Deleted {self.cursor.rowcount} record(s)")

        except Exception as e:
            self.cursor.connection.rollback()
            Debug.log(f"Database error during delete many: {str(e)}")
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    message=Messages.DB_ERROR,
                    data=None
                )
            )