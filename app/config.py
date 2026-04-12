from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    allowed_user_ids_raw: str = Field(alias="ALLOWED_USER_IDS")
    default_channel_id: int = Field(alias="DEFAULT_CHANNEL_ID")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def allowed_user_ids(self) -> List[int]:
        items = [x.strip() for x in self.allowed_user_ids_raw.split(",") if x.strip()]
        return [int(x) for x in items]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
