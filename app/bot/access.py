from aiogram.types import CallbackQuery, Message

from app.utils.config import Settings


def is_allowed(user_id: int, settings: Settings) -> bool:
    return user_id in settings.allowed_user_ids


async def reject_message_if_not_allowed(message: Message, settings: Settings) -> bool:
    if not is_allowed(message.from_user.id, settings):
        await message.answer("У вас нет доступа к этому боту.")
        return True
    return False


async def reject_callback_if_not_allowed(callback: CallbackQuery, settings: Settings) -> bool:
    if not is_allowed(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return True
    return False
