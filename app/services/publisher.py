from aiogram import Bot
from aiogram.types import Message

from app.schemas.draft import DraftPost


class PublisherService:
    async def publish(self, bot: Bot, chat_id: int, draft: DraftPost) -> Message:
        return await bot.send_photo(
            chat_id=chat_id,
            photo=draft.photo_file_id,
            caption=draft.build_publish_caption(),
        )
