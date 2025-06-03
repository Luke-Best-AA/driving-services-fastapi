import sys
import importlib

import pytest

def reload_config(monkeypatch, env_vars):
    # Clear config from sys.modules to force reload
    sys.modules.pop("app.config", None)
    # Set environment variables
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
    # Unset variables not in env_vars
    for k in ["ENV", "SERVER", "DATABASE", "DB_USERNAME", "DB_PASSWORD"]:
        if k not in env_vars:
            monkeypatch.delenv(k, raising=False)
    # Reload config
    config = importlib.import_module("app.config")
    return config

def test_config_prod(monkeypatch):
    env_vars = {
        "ENV": "prod",
        "SERVER": "prod_server",
        "DATABASE": "prod_db",
        "DB_USERNAME": "user",
        "DB_PASSWORD": "pass"
    }
    config = reload_config(monkeypatch, env_vars)
    assert config.ENV == "prod"
    assert config.SERVER == "prod_server"
    assert config.DATABASE == "prod_db"
    assert config.DB_USERNAME == "user"
    assert config.DB_PASSWORD == "pass"
    assert config.TRUSTED_CONNECTION is False

def test_config_dev(monkeypatch):
    env_vars = {
        "ENV": "dev",
        "SERVER": "dev_server",
        "DATABASE": "dev_db"
    }
    config = reload_config(monkeypatch, env_vars)
    assert config.ENV == "dev"
    assert config.SERVER == "dev_server"
    assert config.DATABASE == "dev_db"
    assert config.DB_USERNAME is None
    assert config.DB_PASSWORD is None
    assert config.TRUSTED_CONNECTION is True

def test_config_default_env(monkeypatch):
    env_vars = {
        "SERVER": "default_server",
        "DATABASE": "default_db"
    }
    config = reload_config(monkeypatch, env_vars)
    assert config.ENV == "dev"
    assert config.SERVER == "default_server"
    assert config.DATABASE == "default_db"
    assert config.DB_USERNAME is None
    assert config.DB_PASSWORD is None
    assert config.TRUSTED_CONNECTION is True

def test_token_expiry_constants(monkeypatch):
    config = reload_config(monkeypatch, {})
    assert config.ACCESS_TOKEN_EXPIRY_MINS == 1
    assert config.REFRESH_TOKEN_EXPIRY_HOURS == 1
