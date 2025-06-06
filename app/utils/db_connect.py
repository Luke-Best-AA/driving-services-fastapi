import pyodbc
import logging
from .debug import Debug

# Custom exception for database connection errors
class DatabaseConnectionError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class DBConnect:
    def __init__(self, server: str, database: str, trusted_connection: bool = True, username: str = None, password: str = None):
        self.server = server
        self.database = database
        self.trusted_connection = trusted_connection
        self.username = username
        self.password = password
        self.connection = None
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def connect(self):
        try:
            if self.trusted_connection:
                self.connection = pyodbc.connect(
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"Trusted_Connection=yes;"
                )
                Debug.log(f"Connected to {self.database} on {self.server} using Windows Authentication.")
            else:
                if not self.username or not self.password:
                    raise DatabaseConnectionError("Username and password must be provided for SQL Server Authentication.")
                self.connection = pyodbc.connect(
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                )
                Debug.log(f"Connected to {self.database} on {self.server} using SQL Server Authentication.")
        except pyodbc.Error as e:
            error_message = f"Error connecting to the database: {e}"
            Debug.log(error_message)
            raise DatabaseConnectionError(error_message)

    def close(self):
        try:
            if self.connection:
                self.connection.close()
                Debug.log(f"Connection to {self.database} on {self.server} closed.")
        except pyodbc.Error as e:
            error_message = f"Error closing the database connection: {e}"
            Debug.log(error_message)
            raise DatabaseConnectionError(error_message)