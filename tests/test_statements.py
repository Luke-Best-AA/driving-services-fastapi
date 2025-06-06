import pytest
from app.utils.statements import (
    SelectStatementExecutor,
    InsertStatementExecutor,
    UpdateStatementExecutor,
    DeleteStatementExecutor,
)
from app.utils.messages import Messages
from app.utils.error_constants import TYPE_CONVERSION_ERROR, UNIQUE_KEY_CONSTRAINT

@pytest.fixture
def mock_cursor(mocker):
    cursor = mocker.Mock()
    cursor.connection = mocker.Mock()
    return cursor

def test_select_statement_executor_success(mock_cursor):
    # Setup
    mock_cursor.description = [("id",), ("name",)]
    mock_cursor.fetchall.return_value = [(1, "Alice"), (2, "Bob")]
    executor = SelectStatementExecutor(mock_cursor)
    # Act
    result = executor.execute_select("SELECT * FROM test")
    # Assert
    assert result == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

def test_select_statement_executor_type_error(mock_cursor):
    executor = SelectStatementExecutor(mock_cursor)
    # Patch the constant to match the error string
    executor.cursor.fetchall.side_effect = Exception(TYPE_CONVERSION_ERROR)
    with pytest.raises(ValueError) as exc:
        executor.execute_select("SELECT * FROM test")
    assert Messages.INVALID_TYPE in str(exc.value)

def test_select_statement_executor_unique_constraint(mock_cursor):
    executor = SelectStatementExecutor(mock_cursor)
    executor.cursor.fetchall.side_effect = Exception(UNIQUE_KEY_CONSTRAINT)
    with pytest.raises(ValueError) as exc:
        executor.execute_select("SELECT * FROM test")
    assert Messages.DUPLICATION_ERROR in str(exc.value)

def test_select_statement_executor_db_error(mock_cursor):
    executor = SelectStatementExecutor(mock_cursor)
    executor.cursor.fetchall.side_effect = Exception("some db error")
    with pytest.raises(ValueError) as exc:
        executor.execute_select("SELECT * FROM test")
    assert Messages.DB_ERROR in str(exc.value)

def test_insert_statement_executor_success(mock_cursor):
    mock_cursor.fetchone.return_value = [42]
    executor = InsertStatementExecutor(mock_cursor)
    result = executor.execute_insert("INSERT INTO test VALUES (1)")
    assert result == 42
    mock_cursor.connection.commit.assert_called_once()

def test_insert_statement_executor_success_params(mock_cursor):
    mock_cursor.fetchone.return_value = [42]
    executor = InsertStatementExecutor(mock_cursor)
    result = executor.execute_insert("INSERT INTO test VALUES (?)", (1))
    assert result == 42
    mock_cursor.connection.commit.assert_called_once()    

def test_insert_statement_executor_unique_constraint(mock_cursor):
    mock_cursor.execute.side_effect = Exception(UNIQUE_KEY_CONSTRAINT)
    executor = InsertStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_insert("INSERT INTO test VALUES (1)")
    assert Messages.DUPLICATION_ERROR in str(exc.value)

def test_insert_statement_executor_type_error(mock_cursor):
    mock_cursor.execute.side_effect = Exception(TYPE_CONVERSION_ERROR)
    executor = InsertStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_insert("INSERT INTO test VALUES (1)")
    assert Messages.INVALID_TYPE in str(exc.value)

def test_insert_statement_executor_db_error(mock_cursor):
    mock_cursor.execute.side_effect = Exception("db error")
    executor = InsertStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_insert("INSERT INTO test VALUES (1)")
    assert Messages.DB_ERROR in str(exc.value)

# test insert many
def test_insert_many_statement_executor_success(mock_cursor):
    mock_cursor.executemany.return_value = None
    executor = InsertStatementExecutor(mock_cursor)
    result = executor.execute_insert_many("INSERT INTO test VALUES (1, 2)")
    assert result is None
    mock_cursor.connection.commit.assert_not_called()

def test_insert_many_statement_executor_success_params(mock_cursor):
    mock_cursor.executemany.return_value = None
    executor = InsertStatementExecutor(mock_cursor)
    result = executor.execute_insert_many("INSERT INTO test VALUES (?)", [(1), (2)])
    assert result is None
    mock_cursor.connection.commit.assert_not_called()

def test_insert_many_statement_executor_unique_constraint(mock_cursor):
    mock_cursor.executemany.side_effect = Exception(UNIQUE_KEY_CONSTRAINT)
    executor = InsertStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_insert_many("INSERT INTO test VALUES (?)", [(1), (2)])
    assert Messages.DUPLICATION_ERROR in str(exc.value)

def test_insert_many_statement_executor_type_error(mock_cursor):
    mock_cursor.executemany.side_effect = Exception(TYPE_CONVERSION_ERROR)
    executor = InsertStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_insert_many("INSERT INTO test VALUES (?)", [(1), (2)])
    assert Messages.INVALID_TYPE in str(exc.value)

def test_insert_many_statement_executor_db_error(mock_cursor):
    mock_cursor.executemany.side_effect = Exception("db error")
    executor = InsertStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_insert_many("INSERT INTO test VALUES (?)", [(1), (2)])
    assert Messages.DB_ERROR in str(exc.value)

def test_update_statement_executor_success(mock_cursor):
    mock_cursor.rowcount = 1
    executor = UpdateStatementExecutor(mock_cursor)
    executor.execute_update("UPDATE test SET name='Alice' WHERE id=1")
    mock_cursor.connection.commit.assert_called_once()

def test_update_statement_executor_success_params(mock_cursor):
    mock_cursor.rowcount = 1
    executor = UpdateStatementExecutor(mock_cursor)
    executor.execute_update("UPDATE test SET name='Alice' WHERE id=?", (1))
    mock_cursor.connection.commit.assert_called_once()

def test_update_statement_executor_not_found(mock_cursor):
    mock_cursor.rowcount = 0
    executor = UpdateStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_update("UPDATE test SET name='Alice' WHERE id=1")
    assert Messages.RECORD_NOT_FOUND in str(exc.value)

def test_update_statement_executor_unique_constraint(mock_cursor):
    mock_cursor.execute.side_effect = Exception(UNIQUE_KEY_CONSTRAINT)
    executor = UpdateStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_update("UPDATE test SET name='Alice' WHERE id=1")
    assert Messages.DUPLICATION_ERROR in str(exc.value)

def test_update_statement_executor_type_error(mock_cursor):
    mock_cursor.execute.side_effect = Exception(TYPE_CONVERSION_ERROR)
    executor = UpdateStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_update("UPDATE test SET name='Alice' WHERE id=1")
    assert Messages.INVALID_TYPE in str(exc.value)

def test_update_statement_executor_db_error(mock_cursor):
    mock_cursor.execute.side_effect = Exception("db error")
    executor = UpdateStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_update("UPDATE test SET name='Alice' WHERE id=1")
    assert Messages.DB_ERROR in str(exc.value)

def test_delete_statement_executor_success_params(mock_cursor):
    mock_cursor.rowcount = 1
    executor = DeleteStatementExecutor(mock_cursor)
    executor.execute_delete("DELETE FROM test WHERE id=?", (1))
    mock_cursor.connection.commit.assert_called_once()

def test_delete_statement_executor_success(mock_cursor):
    mock_cursor.rowcount = 1
    executor = DeleteStatementExecutor(mock_cursor)
    executor.execute_delete("DELETE FROM test WHERE id=1")
    mock_cursor.connection.commit.assert_called_once()

def test_delete_statement_executor_not_found(mock_cursor):
    mock_cursor.rowcount = 0
    executor = DeleteStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_delete("DELETE FROM test WHERE id=1")
    assert Messages.RECORD_NOT_FOUND in str(exc.value)

def test_delete_statement_executor_db_error(mock_cursor):
    mock_cursor.execute.side_effect = Exception("db error")
    executor = DeleteStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_delete("DELETE FROM test WHERE id=1")
    assert Messages.DB_ERROR in str(exc.value)

def test_delete_many_statement_executor_success(mock_cursor):
    mock_cursor.rowcount = 1
    executor = DeleteStatementExecutor(mock_cursor)
    executor.execute_delete_many("DELETE FROM test WHERE id=1")
    mock_cursor.connection.commit.assert_called_once()

def test_delete_many_statement_executor_success_params(mock_cursor):
    mock_cursor.rowcount = 1
    executor = DeleteStatementExecutor(mock_cursor)
    executor.execute_delete_many("DELETE FROM test WHERE id=?", [(1), (2)])
    mock_cursor.connection.commit.assert_called_once()

def test_delete_many_statement_executor_db_error(mock_cursor):
    mock_cursor.rowcount = -1
    mock_cursor.executemany.side_effect = Exception("db error")
    executor = DeleteStatementExecutor(mock_cursor)
    with pytest.raises(ValueError) as exc:
        executor.execute_delete_many("DELETE FROM test WHERE id=?", [(1), (2)], False)
    assert Messages.DB_ERROR in str(exc.value)