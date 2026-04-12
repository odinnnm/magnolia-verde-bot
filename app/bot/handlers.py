from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.access import reject_callback_if_not_allowed, reject_message_if_not_allowed
from app.bot.keyboards import make_preview_keyboard
from app.fsm.states import DraftCreation
from app.schemas.draft import DraftPost
from app.services.container import ServiceContainer
from app.utils.config import Settings


def setup_router(services: ServiceContainer, settings: Settings) -> Router:
    router = Router(name="magnolia_verde")

    async def get_draft(state: FSMContext) -> DraftPost | None:
        data = await state.get_data()
        raw_draft = data.get("draft")
        if not raw_draft:
            return None
        return DraftPost.model_validate(raw_draft)

    async def save_draft_to_state(state: FSMContext, draft: DraftPost) -> None:
        await state.update_data(draft=draft.model_dump(mode="json"))

    async def update_preview(callback: CallbackQuery, draft: DraftPost) -> None:
        await callback.message.edit_caption(
            caption=draft.build_preview_text(),
            reply_markup=make_preview_keyboard().as_markup(),
        )

    @router.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        await state.clear()
        await message.answer(
            "Привет! Я MVP-бот Магнолия Верде.\n\n"
            "Команды:\n"
            "/new — создать новый пост\n"
            "/drafts — показать сохранённые черновики\n"
            "/help — список команд\n"
            "/cancel — сбросить текущий сценарий"
        )

    @router.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        await message.answer(
            "Доступные команды:\n"
            "/start — приветствие\n"
            "/new — новый пост\n"
            "/drafts — последние черновики из БД\n"
            "/settings — текущие настройки запуска\n"
            "/cancel — отмена текущего сценария"
        )

    @router.message(Command("settings"))
    async def cmd_settings(message: Message) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        await message.answer(
            "Текущая конфигурация:\n"
            f"• Канал публикации: `{settings.default_channel_id}`\n"
            f"• Postgres: `{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}`\n"
            f"• Redis: `{settings.redis_host}:{settings.redis_port}/{settings.redis_db}`",
            parse_mode="Markdown",
        )

    @router.message(Command("new"))
    async def cmd_new(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        await state.clear()
        await state.set_state(DraftCreation.waiting_for_photo)
        await message.answer("Отправьте фото цветка или букета.")

    @router.message(Command("drafts"))
    async def cmd_drafts(message: Message) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        drafts = await services.draft_repository.list_user_drafts(message.from_user.id)
        if not drafts:
            await message.answer("Сохранённых черновиков пока нет.")
            return

        lines = ["Последние черновики:"]
        for draft in drafts:
            lines.append(
                f"• #{draft.id} [{draft.status.value}] {draft.object_type or 'композиция'}"
            )
        await message.answer("\n".join(lines))

    @router.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        await state.clear()
        await message.answer("Текущий сценарий сброшен.")

    @router.message(DraftCreation.waiting_for_photo, F.photo)
    @router.message(F.photo)
    async def handle_photo(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return

        photo = message.photo[-1]
        await state.set_state(DraftCreation.analyzing_photo)
        await message.answer("Обрабатываю фото…")

        analysis = await services.photo_analyzer.analyze_photo(message)
        draft = services.draft_factory.create_from_analysis(
            photo_file_id=photo.file_id,
            analysis=analysis,
        )
        await save_draft_to_state(state, draft)
        await state.set_state(None)

        await message.answer_photo(
            photo=draft.photo_file_id,
            caption=draft.build_preview_text(),
            reply_markup=make_preview_keyboard().as_markup(),
        )

    @router.message(DraftCreation.waiting_for_price, F.text)
    async def receive_price(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await state.clear()
            await message.answer("Черновик не найден. Начните заново через /new.")
            return
        draft.price_text = services.draft_factory.normalize_price(message.text)
        await save_draft_to_state(state, draft)
        await state.set_state(None)
        await message.answer_photo(
            photo=draft.photo_file_id,
            caption=draft.build_preview_text(),
            reply_markup=make_preview_keyboard().as_markup(),
        )

    @router.message(DraftCreation.waiting_for_manual_caption, F.text)
    async def receive_manual_caption(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await state.clear()
            await message.answer("Черновик не найден. Начните заново через /new.")
            return
        draft.caption = message.text.strip()
        await save_draft_to_state(state, draft)
        await state.set_state(None)
        await message.answer_photo(
            photo=draft.photo_file_id,
            caption=draft.build_preview_text(),
            reply_markup=make_preview_keyboard().as_markup(),
        )

    @router.callback_query(F.data == "shorten")
    async def cb_shorten(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        draft.caption = services.caption.shorten_caption(draft.caption)
        await save_draft_to_state(state, draft)
        await update_preview(callback, draft)
        await callback.answer("Сократил")

    @router.callback_query(F.data == "premium")
    @router.callback_query(F.data == "regenerate")
    async def cb_regenerate(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        draft.caption = services.caption.generate_caption(draft.to_analysis(), premium=True)
        await save_draft_to_state(state, draft)
        await update_preview(callback, draft)
        await callback.answer("Подпись обновлена")

    @router.callback_query(F.data == "add_price")
    async def cb_add_price(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        await state.set_state(DraftCreation.waiting_for_price)
        await callback.answer()
        await callback.message.reply("Отправьте цену, например: 4500")

    @router.callback_query(F.data == "add_story")
    async def cb_add_story(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        draft.story_text = services.caption.build_story(draft.to_analysis())
        await save_draft_to_state(state, draft)
        await update_preview(callback, draft)
        await callback.answer("Историю добавил")

    @router.callback_query(F.data == "edit_caption")
    async def cb_edit_caption(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        await state.set_state(DraftCreation.waiting_for_manual_caption)
        await callback.answer()
        await callback.message.reply("Отправьте новый текст подписи целиком.")

    @router.callback_query(F.data == "save_draft")
    async def cb_save_draft(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        record = await services.draft_repository.save_draft(
            user_id=callback.from_user.id,
            draft=draft,
        )
        await callback.answer("Черновик сохранён")
        await callback.message.reply(f"Черновик сохранён в PostgreSQL с id {record.id}.")

    @router.callback_query(F.data == "publish")
    async def cb_publish(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return

        await services.publisher.publish(bot=bot, chat_id=settings.default_channel_id, draft=draft)
        await services.draft_repository.save_draft(
            user_id=callback.from_user.id,
            draft=draft,
            status="published",
        )
        await state.clear()
        await callback.answer("Опубликовано")
        await callback.message.reply("Готово: пост отправлен в канал.")

    @router.callback_query(F.data == "cancel")
    async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        await state.clear()
        await callback.answer("Отменено")
        await callback.message.reply("Черновик удалён.")

    @router.message()
    async def fallback_message(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        current_state = await state.get_state()
        if current_state == DraftCreation.waiting_for_photo.state:
            await message.answer("Сейчас жду фото. Отправьте изображение или используйте /cancel.")
            return
        await message.answer("Не понял сообщение. Используйте /new для нового поста или /help для списка команд.")

    return router
