from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from sqlalchemy.engine import URL, make_url


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )
    # OpenRouter (sole LLM provider)
    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-v4-pro"

    # Pipeline
    reviewer_temperature: float = 0.3
    deterministic_temperature: float = 0.0
    self_consistency_runs: int = 3
    max_document_chars: int = 200000
    max_section_chars: int = 15000
    max_upload_bytes: int = 10 * 1024 * 1024

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    app_environment: Literal["development", "test", "production"] = "development"
    secret_key: str = "change_me"
    frontend_url: str = "http://localhost:5173"
    enable_api_docs: bool = True
    log_to_file: bool = True

    # Authentication
    auth_cookie_name: str = "assessment_session"
    auth_token_expire_minutes: int = 60 * 24 * 7
    auth_cookie_secure: bool = False
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Database
    postgres_user: str = "eval_user"
    postgres_password: str = "eval_password"
    postgres_db: str = "eval_platform"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_dsn: str = Field(default="", validation_alias="DATABASE_URL")
    database_ssl_required: bool = False

    @field_validator("self_consistency_runs")
    @classmethod
    def _self_consistency_runs_must_be_odd_and_complete(cls, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 3 or value % 2 == 0:
            raise ValueError("self_consistency_runs must be an odd integer of at least 3")
        return value

    @field_validator("max_upload_bytes")
    @classmethod
    def _max_upload_bytes_must_be_positive(cls, value: int) -> int:
        if isinstance(value, bool) or value <= 0:
            raise ValueError("max_upload_bytes must be a positive integer")
        return value

    @model_validator(mode="after")
    def _validate_production_settings(self):
        if self.app_environment != "production":
            return self

        problems = []
        if self.app_debug:
            problems.append("APP_DEBUG must be false")
        if self.secret_key in {"", "change_me", "replace_with_a_long_random_secret_string"}:
            problems.append("SECRET_KEY must be replaced")
        elif len(self.secret_key) < 32:
            problems.append("SECRET_KEY must contain at least 32 characters")
        if not self.openrouter_api_key or self.openrouter_api_key == "your_openrouter_api_key_here":
            problems.append("OPENROUTER_API_KEY must be configured")
        if not self.auth_cookie_secure:
            problems.append("AUTH_COOKIE_SECURE must be true")
        if not self.frontend_url.lower().startswith("https://"):
            problems.append("FRONTEND_URL must use HTTPS")
        if self.enable_api_docs:
            problems.append("ENABLE_API_DOCS must be false")
        if self.log_to_file:
            problems.append("LOG_TO_FILE must be false; use container stdout/stderr")
        if self.google_client_id and not self.google_redirect_uri.lower().startswith("https://"):
            problems.append("GOOGLE_REDIRECT_URI must use HTTPS when Google sign-in is enabled")

        if problems:
            raise ValueError("Unsafe production settings: " + "; ".join(problems))
        return self

    @property
    def database_url(self) -> str:
        if self.database_dsn:
            url = make_url(self.database_dsn)
            if url.get_backend_name() != "postgresql":
                raise ValueError("DATABASE_URL must use PostgreSQL")
            url = url.set(drivername="postgresql+asyncpg")
        else:
            url = URL.create(
                drivername="postgresql+asyncpg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                database=self.postgres_db,
            )

        if self.database_ssl_required:
            query = dict(url.query)
            ssl_mode = query.pop("sslmode", None)
            query.setdefault("ssl", ssl_mode or "require")
            url = url.set(query=query)

        return url.render_as_string(hide_password=False)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
