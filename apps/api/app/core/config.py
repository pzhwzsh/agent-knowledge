from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: Literal["development", "test", "production"] = "development"
    app_secret_key: str = Field(min_length=8)
    database_url: PostgresDsn | str
    redis_url: RedisDsn | str = "redis://redis:6379/0"
    jwt_expire_minutes: int = 60 * 24 * 7
    celery_timezone: str = "Asia/Shanghai"
    celery_cleanup_interval_minutes: int = 30
    celery_daily_sources_hour: int = 8
    celery_daily_sources_minute: int = 30
    celery_default_retry_delay_seconds: int = 60
    celery_max_retries: int = 3

    llm_provider: str = "openai_compatible"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    embedding_model: str | None = None

    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 465
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    dingtalk_webhook: str | None = None
    frontend_url: AnyHttpUrl | str = "http://localhost:3000"
    backend_url: AnyHttpUrl | str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("app_secret_key")
    @classmethod
    def reject_empty_secret(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("APP_SECRET_KEY must not be empty")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
