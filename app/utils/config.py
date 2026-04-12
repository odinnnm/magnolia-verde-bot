from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    allowed_user_ids_raw: str = Field(alias="ALLOWED_USER_IDS")
    default_channel_id: int = Field(alias="DEFAULT_CHANNEL_ID")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    app_env: str = Field(default="local", alias="APP_ENV")

    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")

    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    @property
    def allowed_user_ids(self) -> list[int]:
        items = [item.strip() for item in self.allowed_user_ids_raw.split(",") if item.strip()]
        return [int(item) for item in items]

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_debug(self) -> bool:
        return self.app_env.lower() in {"local", "dev", "debug"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
