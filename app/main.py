import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

bot = Bot(token=settings.bot_token)
dp = Dispatcher()


@dataclass
class DraftPost:
    photo_file_id: str
    object_type: str
    flowers: list[str]
    colors: list[str]
    style_tags: list[str]
    caption: str
    price_text: Optional[str] = None


DRAFTS_BY_USER: dict[int, DraftPost] = {}


def is_allowed(user_id: int) -> bool:
    return user_id in settings.allowed_user_ids


def make_preview_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Опубликовать", callback_data="publish"),
        InlineKeyboardButton(text="Сделать короче", callback_data="shorten"),
    )
    kb.row(
        InlineKeyboardButton(text="Добавить цену", callback_data="add_price"),
        InlineKeyboardButton(text="Перегенерировать", callback_data="regenerate"),
    )
    kb.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    return kb


async def reject_if_not_allowed(message: Message) -> bool:
    if not is_allowed(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        return True
    return False


async def reject_callback_if_not_allowed(callback: CallbackQuery) -> bool:
    if not is_allowed(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return True
    return False


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    await message.answer(
        "Привет! Я MVP-бот Магнолия Верде.\n\n"
        "Команды:\n"
        "/new — создать новый пост\n"
        "/cancel — удалить текущий черновик"
    )


@dp.message(Command("new"))
async def cmd_new(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    DRAFTS_BY_USER.pop(message.from_user.id, None)
    await message.answer("Отправьте фото цветка или букета.")


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return
    DRAFTS_BY_USER.pop(message.from_user.id, None)
    await message.answer("Текущий черновик удалён.")


@dp.message(F.photo)
async def handle_photo(message: Message) -> None:
    if await reject_if_not_allowed(message):
        return

    photo = message.photo[-1]
    await message.answer("Обрабатываю фото…")

    analysis = mock_analyze_photo(message)
    caption = generate_caption(analysis)

    draft = DraftPost(
        photo_file_id=photo.file_id,
        object_type=analysis["object_type"],
        flowers=analysis["flowers"],
        colors=analysis["colors"],
        style_tags=analysis["style_tags"],
        caption=caption,
    )
    DRAFTS_BY_USER[message.from_user.id] = draft

    summary = (
        f"Распознано:\n"
        f"• Тип: {draft.object_type}\n"
        f"• Цветы: {', '.join(draft.flowers)}\n"
        f"• Палитра: {', '.join(draft.colors)}\n"
        f"• Стиль: {', '.join(draft.style_tags)}\n\n"
        f"Предпросмотр подписи:\n{draft.caption}"
    )
    await message.answer_photo(
        photo=draft.photo_file_id,
        caption=summary,
        reply_markup=make_preview_keyboard().as_markup(),
    )


@dp.callback_query(F.data == "shorten")
async def cb_shorten(callback: CallbackQuery) -> None:
    if await reject_callback_if_not_allowed(callback):
        return
    draft = DRAFTS_BY_USER.get(callback.from_user.id)
    if not draft:
        await callback.answer("Черновик не найден", show_alert=True)
        return
    draft.caption = shorten_caption(draft.caption)
    await callback.message.edit_caption(
        caption=build_preview_text(draft),
        reply_markup=make_preview_keyboard().as_markup(),
    )
    await callback.answer("Сократил")


@dp.callback_query(F.data == "regenerate")
async def cb_regenerate(callback: CallbackQuery) -> None:
    if await reject_callback_if_not_allowed(callback):
        return
    draft = DRAFTS_BY_USER.get(callback.from_user.id)
    if not draft:
        await callback.answer("Черновик не найден", show_alert=True)
        return
    draft.caption = generate_caption(
        {
            "object_type": draft.object_type,
            "flowers": draft.flowers,
            "colors": draft.colors,
            "style_tags": draft.style_tags,
        },
        premium=True,
    )
    await callback.message.edit_caption(
        caption=build_preview_text(draft),
        reply_markup=make_preview_keyboard().as_markup(),
    )
    await callback.answer("Перегенерировал")


@dp.callback_query(F.data == "add_price")
async def cb_add_price(callback: CallbackQuery) -> None:
    if await reject_callback_if_not_allowed(callback):
        return
    draft = DRAFTS_BY_USER.get(callback.from_user.id)
    if not draft:
        await callback.answer("Черновик не найден", show_alert=True)
        return
    draft.price_text = "Стоимость: 4500 ₽"
    await callback.message.edit_caption(
        caption=build_preview_text(draft),
        reply_markup=make_preview_keyboard().as_markup(),
    )
    await callback.answer("Добавил пример цены")


@dp.callback_query(F.data == "publish")
async def cb_publish(callback: CallbackQuery) -> None:
    if await reject_callback_if_not_allowed(callback):
        return
    draft = DRAFTS_BY_USER.get(callback.from_user.id)
    if not draft:
        await callback.answer("Черновик не найден", show_alert=True)
        return

    post_text = draft.caption
    if draft.price_text:
        post_text += f"\n\n{draft.price_text}"
    post_text += "\n\nМагнолия Верде"

    await bot.send_photo(
        chat_id=settings.default_channel_id,
        photo=draft.photo_file_id,
        caption=post_text,
    )
    DRAFTS_BY_USER.pop(callback.from_user.id, None)
    await callback.answer("Опубликовано")
    await callback.message.reply("Готово: пост отправлен в канал.")


@dp.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery) -> None:
    if await reject_callback_if_not_allowed(callback):
        return
    DRAFTS_BY_USER.pop(callback.from_user.id, None)
    await callback.answer("Отменено")
    await callback.message.reply("Черновик удалён.")


def mock_analyze_photo(message: Message) -> dict:
    return {
        "object_type": "букет",
        "flowers": ["роза", "эустома", "диантус"],
        "colors": ["белый", "розовый"],
        "style_tags": ["нежный", "воздушный"],
    }


def generate_caption(analysis: dict, premium: bool = False) -> str:
    base = (
        f"Нежный авторский {analysis['object_type']} в палитре {', '.join(analysis['colors'])}. "
        f"В композиции просматриваются {', '.join(analysis['flowers'])}. "
        f"Подойдёт для комплимента, дня рождения или красивого знака внимания."
    )
    if premium:
        return base + " Элегантная фактура и более выразительное настроение делают композицию особенно эффектной."
    return base


def shorten_caption(text: str) -> str:
    parts = text.split(". ")
    return ". ".join(parts[:2]).strip()


def build_preview_text(draft: DraftPost) -> str:
    preview = (
        f"Распознано:\n"
        f"• Тип: {draft.object_type}\n"
        f"• Цветы: {', '.join(draft.flowers)}\n"
        f"• Палитра: {', '.join(draft.colors)}\n"
        f"• Стиль: {', '.join(draft.style_tags)}\n\n"
        f"Предпросмотр подписи:\n{draft.caption}"
    )
    if draft.price_text:
        preview += f"\n\n{draft.price_text}"
    return preview


async def main() -> None:
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
