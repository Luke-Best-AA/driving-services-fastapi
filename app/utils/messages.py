class Messages:
    # General messages
    NO_CHANGE = "No changes detected"
    INVALID_FIELD = "Invalid field: {}"
    INVALID_FIELD_VALUE = "Invalid: {} {}"
    INVALID_TYPE = "Invalid type for field"
    FIELD_REQUIRED = "Field '{}' is required"
    DUPLICATION_ERROR = "Duplicate entry"
    RECORD_NOT_FOUND = "Record not found"
    API_IS_RUNNNG = "API is running"
    INVALID_REQUEST_DATA = "Invalid request data"
    AUTHORIZATION_HEADER_MISSING = "Authorization header missing or invalid"

    # Token-related messages
    REFRESH_TOKEN_EXPIRED = "Refresh token has expired"
    INVALID_REFRESH_TOKEN = "Invalid refresh token"
    TOKEN_HAS_EXPIRED = "Token has expired"
    INVALID_TOKEN = "Invalid token"
    TOKEN_VERIFICATION_FAILED = "Token verification failed"
    TOKEN_VERIFICATION_SUCCESS = "Token verification successful"

    # User-related messages
    USER_NOT_FOUND = "User not found"
    USER_NO_PERMISSION = "User does not have permission to access this resource"
    USER_NO_PERMISSION_CHANGE = "User does not have permission to make this change"
    USER_INVALID_CREDENTIALS = "Invalid username or password"
    USER_CREATED_SUCCESS = "User created successfully"
    USER_READ_SUCCESS = "User(s) retrieved successfully"
    USER_UPDATED_SUCCESS = "User updated successfully"
    USER_DELETED_SUCCESS = "User deleted successfully"
    USER_INVALID_READ_MODE = "Invalid mode. Use 'list_all', 'filter', 'by_id' or 'myself'."
    USER_PASSWORD_UPDATED_SUCCESS = "User password updated successfully"

    # Optional Extra-related messages
    OPTIONAL_EXTRA_NOT_FOUND = "Optional extra not found"
    OPTIONAL_EXTRAS_NOT_FOUND = "Optional extras with ID(s) {} not found"
    OPTIONAL_EXTRA_CREATED_SUCCESS = "Optional extra created successfully"
    OPTIONAL_EXTRA_READ_SUCCESS = "Optional extra(s) retrieved successfully"
    OPTIONAL_EXTRA_UPDATED_SUCCESS = "Optional extra updated successfully"
    OPTIONAL_EXTRA_DELETED_SUCCESS = "Optional extra deleted successfully"
    OPTIONAL_EXTRA_INVALID_READ_MODE = "Invalid mode. Use 'list_all' or 'by_id'."

    # Policy-related messages
    POLICY_NOT_FOUND = "Policy not found"
    POLICY_NO_PERMISSION = "User does not own this policy"
    POLICY_CREATED_SUCCESS = "Policy created successfully"
    POLICY_READ_SUCCESS = "Policy(s) retrieved successfully"
    POLICY_UPDATED_SUCCESS = "Policy updated successfully"
    POLICY_DELETED_SUCCESS = "Policy deleted successfully"

    # Database-related messages
    DB_ERROR = "An error occurred while interacting with the database"
    DB_CONNECTION_FAILED = "Failed to connect to the database"