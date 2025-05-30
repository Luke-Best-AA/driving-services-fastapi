from http import HTTPStatus
from ..statements import InsertStatementExecutor, UpdateStatementExecutor, DeleteStatementExecutor, SelectStatementExecutor
from ..response import APIResponse
from ..user import User
from ..debug import Debug  # Import the Debug class
from ..messages import Messages  # Import the Messages class

class UserService:
    def __init__(self, cursor):
        """
        Initializes the UserService with a database cursor.

        :param cursor: A database cursor object for executing queries.
        """
        self.cursor = cursor

    async def get_user_by_id(self, user_id: int, requesting_user: User = None, password: bool = False, format: bool = False):
        if requesting_user and not requesting_user.is_admin and requesting_user.user_id != user_id:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.FORBIDDEN,
                    message=Messages.USER_NO_PERMISSION,
                    data=None
                )
            )

        executor = SelectStatementExecutor(self.cursor)
        sql = "SELECT * FROM Users WHERE user_id = ?"
        user_data = executor.execute_select(sql, (user_id))
        self.error_not_found(user_data)
        # Convert the first row to a User object
        user = User(**user_data[0])
        # If password is not requested, set it to None
        if not password:
            user.password = None

        if format:
            user = self.format_users([user_data[0]])
        return user

    async def authenticate_user(self, username: str, password: str):
        executor = SelectStatementExecutor(self.cursor)
        sql = "SELECT * FROM Users WHERE username = ? AND password = ?"
        user_data = executor.execute_select(sql, (username, password))
        if not user_data:
            Debug.log("Invalid credentials")
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.UNAUTHORIZED,
                    message=Messages.USER_INVALID_CREDENTIALS,
                    data=None
                )
            )
        user = User(**user_data[0])
        user.password = None
        return user

    async def create_user(self, user: User):
        """
        Creates a new user in the database.

        :param user: The User object containing the details to insert.
        :return: The created user with its ID.
        """
        executor = InsertStatementExecutor(self.cursor)
        sql = """
            INSERT INTO Users (username, password, email, is_admin)
            OUTPUT INSERTED.user_id
            VALUES (?, ?, ?, ?)
        """
        user.user_id = executor.execute_insert(sql, (user.username, user.password, user.email, user.is_admin))
        user.password = None  # Do not expose the password in the response
        return user

    async def update_user(self, updated_user: User):
        """
        Updates an existing user in the database.

        :param updated_user: The updated User object.
        """
        # Check if the user exists
        existing_user = await self.get_user_by_id(updated_user.user_id, password=True)

        if not existing_user:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.NOT_FOUND,
                    message=Messages.USER_NOT_FOUND,
                    data=None
                )
            )

        # Check if there are changes
        if existing_user == updated_user:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    message=Messages.NO_CHANGE,
                    data=None
                )
            )

        # Update the user
        executor = UpdateStatementExecutor(self.cursor)
        sql = """
            UPDATE Users
            SET username = ?, email = ?, is_admin = ?
            WHERE user_id = ?
        """
        executor.execute_update(sql, (updated_user.username, updated_user.email, updated_user.is_admin, updated_user.user_id))

    async def update_user_password(self, user_id: int, new_password: str):
        """
        Updates the password of an existing user in the database.

        :param user_id: The ID of the user to update.
        :param new_password: The new password to set for the user.
        """
        # Check if the user exists
        user = await self.get_user_by_id(user_id, password=True)

        if not user:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.NOT_FOUND,
                    message=Messages.USER_NOT_FOUND,
                    data=None
                )
            )

        # Update the user's password
        executor = UpdateStatementExecutor(self.cursor)
        sql = "UPDATE Users SET password = ? WHERE user_id = ?"
        executor.execute_update(sql, (new_password, user_id))

    async def delete_user(self, user_id: int):
        """
        Deletes a user from the database.

        :param user_id: The ID of the user to delete.
        """
        # Check if the user exists
        user = await self.get_user_by_id(user_id)

        if not user:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.NOT_FOUND,
                    message=Messages.USER_NOT_FOUND,
                    data=None
                )
            )

        # Delete the user
        executor = DeleteStatementExecutor(self.cursor)
        sql = "DELETE FROM Users WHERE user_id = ?"
        executor.execute_delete(sql, (user_id))

    def check_admin(self, user: User):
        if not user.is_admin:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.FORBIDDEN,
                    message=Messages.USER_NO_PERMISSION,
                    data=None
                )
            )
        return True
    
    def check_update_permissions(self, user: User, target_user_id, throw_exception=True):
        if not user.is_admin and user.user_id != target_user_id:
            if throw_exception:
                raise ValueError(
                    APIResponse(
                        status=HTTPStatus.FORBIDDEN,
                        message=Messages.USER_NO_PERMISSION_CHANGE,
                        data=None
                    )
                )
            else:
                Debug.log(f"User {user.user_id} does not have permission to update")
                return False
        return True
    
    async def check_user_owns_policy(self, user: User, policy_id):
        sql = "SELECT * FROM CarInsurancePolicy WHERE user_id = ? AND ci_policy_id = ?"
        result = SelectStatementExecutor(self.cursor).execute_select(sql, (user.user_id, policy_id))
        return len(result) > 0
    
    def verify_password(self, existing_password: str, provided_password: str):
        """
        Verifies if the provided password matches the existing password.

        :param existing_password: The existing password stored in the database.
        :param provided_password: The password provided by the user for verification.
        :return: True if the passwords match, False otherwise.
        """
        return existing_password == provided_password
    
    async def list_all_users(self, requesting_user):
        self.check_admin(requesting_user)
        users = SelectStatementExecutor(self.cursor).execute_select("SELECT * FROM Users")
        self.error_not_found(users)
        return self.format_users(users)

    async def filter_users(self, requesting_user, field, value):
        self.check_admin(requesting_user)

        # Validate if the field exists in the Users table
        valid_fields = set(User.__annotations__.keys())  # Dynamically get valid fields from User model
        if field not in valid_fields:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    message=Messages.INVALID_FIELD.format(field),
                    data=None
                )
            )
        users = SelectStatementExecutor(self.cursor).execute_select(f"SELECT * FROM Users WHERE {field} = ?", (value))
        self.error_not_found(users)

        return self.format_users(users)

    def error_not_found(self, users):
        if not users:
            raise ValueError(
                APIResponse(
                    status=HTTPStatus.NOT_FOUND,
                    message=Messages.USER_NOT_FOUND,
                    data=None
                )
            )

    def format_users(self, users):
        return [
            User(
                user_id=user["user_id"],
                username=user["username"],
                password=None,  # Password is not exposed
                email=user["email"],
                is_admin=user["is_admin"]
            ).model_dump()
            for user in users
        ]    