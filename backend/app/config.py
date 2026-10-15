from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "DocSage"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+asyncpg://docsage:docsage@localhost:5432/docsage"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    storage_path: str = "./data/storage"
    max_upload_mb: int = 50

    jwt_secret_key: str = Field(default="change-me-in-production-use-openssl-rand-hex-32")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_seconds: float = 60.0


    log_level: str = "INFO"
    log_json: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
