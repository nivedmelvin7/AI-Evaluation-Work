import pytest
from pydantic import ValidationError

from app.config import Settings


def test_default_upload_limit_is_ten_mibibytes():
    assert Settings().max_upload_bytes == 10 * 1024 * 1024


def test_database_url_encodes_credentials_safely():
    settings = Settings(
        postgres_user="user@example.com",
        postgres_password="pa:ss/word",
        postgres_host="db",
    )

    assert "user%40example.com" in settings.database_url
    assert "pa%3Ass%2Fword" in settings.database_url


def test_database_url_normalises_managed_postgres_and_ssl():
    settings = Settings(
        database_dsn="postgresql://user:password@db.example.com/evaluations?sslmode=require",
        database_ssl_required=True,
    )

    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert "ssl=require" in settings.database_url
    assert "sslmode" not in settings.database_url


def test_production_rejects_insecure_defaults():
    with pytest.raises(ValidationError, match="Unsafe production settings"):
        Settings(app_environment="production")


def test_secure_production_settings_are_accepted():
    settings = Settings(
        app_environment="production",
        app_debug=False,
        secret_key="x" * 48,
        openrouter_api_key="configured-key",
        auth_cookie_secure=True,
        frontend_url="https://evaluation.example.com",
        enable_api_docs=False,
        log_to_file=False,
    )

    assert settings.app_environment == "production"
