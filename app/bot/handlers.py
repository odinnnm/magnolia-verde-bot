import logging
from uuid import UUID

from aiogram import Bot, F, Router
from aiogram.types.error_event import ErrorEvent
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.models import PostStatus
from app.bot.access import reject_callback_if_not_allowed, reject_message_if_not_allowed
from app.bot.keyboards import make_preview_keyboard
from app.fsm.states import DraftCreation
from app.schemas.draft import DraftPost
from app.services.container import ServiceContainer
from app.utils.config import Settings

logger = logging.getLogger(__name__)


def setup_router(services: ServiceContainer, settings: Settings) -> Router:
    router = Router(name="magnolia_verde")

    async def get_post_id(state: FSMContext) -> UUID | None:
        data = await state.get_data()
        raw_post_id = data.get("post_id")
        if not raw_post_id:
            return None
        return UUID(raw_post_id)

    async def get_draft(state: FSMContext) -> DraftPost | None:
        data = await state.get_data()
        raw_draft = data.get("draft")
        if not raw_draft:
            return None
        return DraftPost.model_validate(raw_draft)

    async def save_context_to_state(state: FSMContext, post_id: UUID, draft: DraftPost) -> None:
        await state.update_data(
            post_id=str(post_id),
            draft=draft.model_dump(mode="json"),
        )

    async def persist_post(
        state: FSMContext,
        draft: DraftPost,
        status: PostStatus | None = None,
    ) -> UUID | None:
        post_id = await get_post_id(state)
        if not post_id:
            return None
        post = await services.post_repository.update_post(post_id=post_id, draft=draft, status=status)
        if not post:
            return None
        await save_context_to_state(state, post.id, draft)
        return post.id

    async def archive_current_post(state: FSMContext) -> None:
        post_id = await get_post_id(state)
        if not post_id:
            return
        await services.post_repository.set_status(post_id, PostStatus.archived)

    async def update_preview(callback: CallbackQuery, draft: DraftPost) -> None:
        await callback.message.edit_caption(
            caption=draft.build_preview_text(),
            reply_markup=make_preview_keyboard().as_markup(),
        )

    @router.error()
    async def on_error(event: ErrorEvent) -> None:
        logger.exception("Unhandled bot error: %s", event.exception)
        update = event.update
        if update.callback_query:
            await update.callback_query.answer("Что-то пошло не так. Попробуйте ещё раз.", show_alert=True)
            return
        if update.message:
            await update.message.answer("Что-то пошло не так. Попробуйте ещё раз позже.")

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
            "/cancel — отмена текущего сценария"
        )

    @router.message(Command("new"))
    async def cmd_new(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        logger.info("Starting new post flow for user_id=%s", message.from_user.id)
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
        await archive_current_post(state)
        await state.clear()
        logger.info("Current flow cancelled by user_id=%s", message.from_user.id)
        await message.answer("Текущий сценарий отменён.")

    @router.message(DraftCreation.waiting_for_photo, F.photo)
    @router.message(F.photo)
    async def handle_photo(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return

        photo = message.photo[-1]
        await state.set_state(DraftCreation.analyzing_photo)
        logger.info("Received photo from user_id=%s", message.from_user.id)
        await message.answer("Обрабатываю фото…")

        user = await services.user_repository.get_or_create(
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        analysis = await services.photo_analyzer.analyze_photo(message)
        draft = services.draft_factory.create_from_analysis(
            photo_file_id=photo.file_id,
            analysis=analysis,
        )
        post = await services.post_repository.create_post(
            user_id=user.id,
            draft=draft,
            status=PostStatus.draft,
        )
        await save_context_to_state(state, post.id, draft)
        await state.set_state(None)

        logger.info("Created draft post_id=%s for user_id=%s", post.id, message.from_user.id)
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
        await persist_post(state, draft)
        await state.set_state(None)
        logger.info("Updated price for user_id=%s", message.from_user.id)
        await message.answer("Цену добавил.")
        await message.answer_photo(
            photo=draft.photo_file_id,
            caption=draft.build_preview_text(),
            reply_markup=make_preview_keyboard().as_markup(),
        )

    @router.message(DraftCreation.waiting_for_availability, F.text)
    async def receive_availability(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await state.clear()
            await message.answer("Черновик не найден. Начните заново через /new.")
            return
        draft.availability_text = services.draft_factory.normalize_availability(message.text)
        await persist_post(state, draft)
        await state.set_state(None)
        logger.info("Updated availability for user_id=%s", message.from_user.id)
        await message.answer("Наличие обновил.")
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
        await persist_post(state, draft)
        await state.set_state(None)
        logger.info("Updated caption manually for user_id=%s", message.from_user.id)
        await message.answer("Текст обновил.")
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
        await persist_post(state, draft, status=PostStatus.ready)
        await update_preview(callback, draft)
        logger.info("Shortened caption for user_id=%s", callback.from_user.id)
        await callback.answer("Сократил")

    @router.callback_query(F.data == "regenerate")
    async def cb_regenerate(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        draft.caption = services.caption.generate_caption(draft.to_analysis(), premium=False)
        await persist_post(state, draft, status=PostStatus.ready)
        await update_preview(callback, draft)
        logger.info("Regenerated caption for user_id=%s", callback.from_user.id)
        await callback.answer("Перегенерировал")

    @router.callback_query(F.data == "premium")
    async def cb_premium(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        draft.caption = services.caption.generate_caption(draft.to_analysis(), premium=True)
        await persist_post(state, draft, status=PostStatus.ready)
        await update_preview(callback, draft)
        logger.info("Premium caption generated for user_id=%s", callback.from_user.id)
        await callback.answer("Сделал премиальнее")

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

    @router.callback_query(F.data == "add_availability")
    async def cb_add_availability(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        await state.set_state(DraftCreation.waiting_for_availability)
        await callback.answer()
        await callback.message.reply(
            "Отправьте наличие, например: В наличии, Под заказ или Ограниченное количество."
        )

    @router.callback_query(F.data == "add_story")
    async def cb_add_story(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        draft.story_text = services.caption.build_story(draft.to_analysis())
        if not draft.story_text:
            await callback.answer("Не удалось уверенно определить историю цветка", show_alert=True)
            return
        await persist_post(state, draft, status=PostStatus.ready)
        await update_preview(callback, draft)
        logger.info("Added story for user_id=%s", callback.from_user.id)
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
        post_id = await get_post_id(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        if not post_id:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        await services.post_repository.update_post(post_id=post_id, draft=draft, status=PostStatus.draft)
        await state.clear()
        logger.info("Saved draft post_id=%s for user_id=%s", post_id, callback.from_user.id)
        await callback.answer("Черновик сохранён")
        await callback.message.reply(f"Черновик сохранён в PostgreSQL с id {post_id}.")

    @router.callback_query(F.data == "publish")
    async def cb_publish(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        draft = await get_draft(state)
        post_id = await get_post_id(state)
        if not draft:
            await callback.answer("Черновик не найден", show_alert=True)
            return
        if not post_id:
            await callback.answer("Черновик не найден", show_alert=True)
            return

        channel = await services.channel_repository.get_or_create(
            telegram_chat_id=settings.default_channel_id,
            title="Magnolia Verde",
            is_default=True,
        )
        sent_message = await services.publisher.publish(
            bot=bot,
            chat_id=settings.default_channel_id,
            draft=draft,
        )
        await services.post_repository.mark_published(
            post_id=post_id,
            published_message_id=sent_message.message_id,
            channel_id=channel.id,
        )
        await state.clear()
        logger.info(
            "Published post_id=%s by user_id=%s message_id=%s",
            post_id,
            callback.from_user.id,
            sent_message.message_id,
        )
        await callback.answer("Опубликовано")
        await callback.message.reply("Готово: пост отправлен в канал.")

    @router.callback_query(F.data == "cancel")
    async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
        if await reject_callback_if_not_allowed(callback, settings):
            return
        await archive_current_post(state)
        await state.clear()
        logger.info("Cancelled current flow by user_id=%s", callback.from_user.id)
        await callback.answer("Отменено")
        await callback.message.reply("Сценарий отменён.")

    @router.message()
    async def fallback_message(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        current_state = await state.get_state()
        if current_state == DraftCreation.waiting_for_photo.state:
            await message.answer("Сейчас жду фото. Отправьте изображение или используйте /cancel.")
            return
        if current_state == DraftCreation.waiting_for_price.state:
            await message.answer("Сейчас жду цену. Отправьте число или используйте /cancel.")
            return
        if current_state == DraftCreation.waiting_for_availability.state:
            await message.answer("Сейчас жду наличие. Отправьте текст или используйте /cancel.")
            return
        if current_state == DraftCreation.waiting_for_manual_caption.state:
            await message.answer("Сейчас жду новый текст подписи. Отправьте сообщение или используйте /cancel.")
            return
        await message.answer("Не понял сообщение. Используйте /new для нового поста или /help для списка команд.")

    return router
