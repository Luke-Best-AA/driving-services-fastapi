import pytest
from app.utils.db_connect import DBConnect, DatabaseConnectionError
import pyodbc

@pytest.fixture
def db_connect():
    """Fixture to create a DBConnect instance."""
    return DBConnect(server="test_server", database="test_database")

def test_db_connect_success(mocker, db_connect):
    # Mock pyodbc.connect to simulate a successful connection
    mocker.patch("pyodbc.connect", return_value=mocker.Mock())

    # Call the connect method
    db_connect.connect()

    # Assert that the connection was established
    assert db_connect.connection is not None

def test_db_connect_failure(mocker, db_connect):
    # Mock pyodbc.connect to raise an error
    mocker.patch("pyodbc.connect", side_effect=pyodbc.Error("Connection failed"))

    # Call the connect method and expect a DatabaseConnectionError
    with pytest.raises(DatabaseConnectionError) as exc_info:
        db_connect.connect()
    assert str(exc_info.value) == "Error connecting to the database: Connection failed"

def test_db_close_success(mocker, db_connect):
    # Mock pyodbc.connect to simulate a successful connection
    mock_connection = mocker.Mock()
    mocker.patch("pyodbc.connect", return_value=mock_connection)

    # Establish the connection
    db_connect.connect()

    # Mock the close method of the connection
    mock_connection.close = mocker.Mock()

    # Call the close method
    db_connect.close()

    # Assert that the close method was called
    mock_connection.close.assert_called_once()

def test_db_close_failure(mocker, db_connect):
    # Mock pyodbc.connect to simulate a successful connection
    mock_connection = mocker.Mock()
    mocker.patch("pyodbc.connect", return_value=mock_connection)

    # Establish the connection
    db_connect.connect()

    # Mock the close method to raise an error
    mock_connection.close = mocker.Mock(side_effect=pyodbc.Error("Close failed"))

    # Call the close method and expect a DatabaseConnectionError
    with pytest.raises(DatabaseConnectionError) as exc_info:
        db_connect.close()
    assert str(exc_info.value) == "Error closing the database connection: Close failed"

def test_db_connect_sql_auth_success(mocker):
    # Mock pyodbc.connect to simulate a successful connection
    mocker.patch("pyodbc.connect", return_value=mocker.Mock())
    db = DBConnect(
        server="sql_server",
        database="sql_db",
        trusted_connection=False,
        username="sql_user",
        password="sql_pass"
    )
    db.connect()
    assert db.connection is not None

def test_db_connect_sql_auth_missing_credentials():
    db = DBConnect(
        server="sql_server",
        database="sql_db",
        trusted_connection=False,
        username=None,
        password=None
    )
    with pytest.raises(DatabaseConnectionError) as exc_info:
        db.connect()
    assert "Username and password must be provided" in str(exc_info.value)

def test_db_connect_sql_auth_failure(mocker):
    # Mock pyodbc.connect to raise an error
    mocker.patch("pyodbc.connect", side_effect=pyodbc.Error("SQL Auth failed"))
    db = DBConnect(
        server="sql_server",
        database="sql_db",
        trusted_connection=False,
        username="sql_user",
        password="sql_pass"
    )
    with pytest.raises(DatabaseConnectionError) as exc_info:
        db.connect()
    assert "Error connecting to the database: SQL Auth failed" in str(exc_info.value)