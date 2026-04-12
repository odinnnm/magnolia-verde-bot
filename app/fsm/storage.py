from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage

from app.utils.config import Settings


def create_fsm_storage(settings: Settings) -> RedisStorage:
    return RedisStorage.from_url(
        settings.redis_dsn,
        key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
    )
