import os
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "dev")

if ENV == "prod":
    SERVER = os.getenv("SERVER")
    DATABASE = os.getenv("DATABASE")
    DB_USERNAME = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    TRUSTED_CONNECTION = False
else:
    SERVER = os.getenv("SERVER")
    DATABASE = os.getenv("DATABASE")
    DB_USERNAME = None
    DB_PASSWORD = None
    TRUSTED_CONNECTION = True

ACCESS_TOKEN_EXPIRY_MINS = 1
REFRESH_TOKEN_EXPIRY_HOURS = 1