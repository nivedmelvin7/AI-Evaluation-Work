from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # OpenRouter (sole LLM provider)
    openrouter_api_key: str = ""
    openrouter_model: str = "qwen/qwen3.7-plus"

    # Pipeline
    reviewer_temperature: float = 0.3
    deterministic_temperature: float = 0.0
    self_consistency_runs: int = 3
    max_document_chars: int = 200000
    max_section_chars: int = 15000

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    secret_key: str = "change_me"

    # Database
    postgres_user: str = "eval_user"
    postgres_password: str = "eval_password"
    postgres_db: str = "eval_platform"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
