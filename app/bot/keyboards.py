from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def make_preview_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Опубликовать", callback_data="publish"),
        InlineKeyboardButton(text="Перегенерировать", callback_data="regenerate"),
    )
    kb.row(
        InlineKeyboardButton(text="Сделать короче", callback_data="shorten"),
        InlineKeyboardButton(text="Сделать премиальнее", callback_data="premium"),
    )
    kb.row(
        InlineKeyboardButton(text="Добавить цену", callback_data="add_price"),
        InlineKeyboardButton(text="Добавить наличие", callback_data="add_availability"),
    )
    kb.row(
        InlineKeyboardButton(text="Добавить историю", callback_data="add_story"),
        InlineKeyboardButton(text="Редактировать вручную", callback_data="edit_caption"),
    )
    kb.row(
        InlineKeyboardButton(text="Сохранить в черновики", callback_data="save_draft"),
        InlineKeyboardButton(text="Отмена", callback_data="cancel"),
    )
    return kb
