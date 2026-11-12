from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str
    postgres_port: int = 5432
    redis_url: str
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"
    cors_origins: list[str] = []
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from_email: str | None = None
    smtp_tls: Literal["starttls", "implicit", "none"] = "starttls"
    telegram_bot_token: SecretStr | None = None
    telegram_manager_chat_id: str | None = None
    telegram_webhook_secret: SecretStr | None = None
    telegram_lead_currency: str = Field(default="RUB", pattern=r"^[A-Z]{3}$")

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
