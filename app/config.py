from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM backend
    llm_backend: str = "groq"

    # Groq
    groq_api_key: str = "not_set"
    groq_primary_model: str = "llama-3.3-70b-versatile"
    groq_fast_model: str = "llama-3.1-8b-instant"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_primary_model: str = "llama3.1:8b"
    ollama_fast_model: str = "llama3.2:3b"

    # Pipeline
    reviewer_temperature: float = 0.3
    deterministic_temperature: float = 0.0
    self_consistency_runs: int = 3
    max_document_chars: int = 80000
    max_section_chars: int = 15000

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    secret_key: str = "change_me"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
