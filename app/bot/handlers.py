import logging
from uuid import UUID

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types.error_event import ErrorEvent

from app.bot.access import reject_callback_if_not_allowed, reject_message_if_not_allowed
from app.bot.keyboards import make_draft_actions_keyboard, make_preview_keyboard
from app.db.models import PostStatus
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

    async def save_context_to_state(state: FSMContext, post_id: UUID, draft: DraftPost) -> None:
        await state.update_data(
            post_id=str(post_id),
            draft=draft.model_dump(mode="json"),
        )

    async def get_current_post(state: FSMContext) -> tuple[UUID | None, DraftPost | None]:
        post_id = await get_post_id(state)
        if not post_id:
            return None, None

        post = await services.post_repository.get_by_id(post_id)
        if not post:
            logger.warning("Post not found in repository for post_id=%s", post_id)
            return post_id, None

        draft = services.post_repository.build_draft_view(post)
        await save_context_to_state(state, post.id, draft)
        return post.id, draft

    async def archive_current_post(state: FSMContext) -> None:
        post_id = await get_post_id(state)
        if not post_id:
            return
        await services.post_repository.set_status(post_id, PostStatus.archived)

    async def update_preview(callback: CallbackQuery, draft: DraftPost) -> bool:
        try:
            await callback.message.edit_caption(
                caption=draft.build_preview_text(),
                reply_markup=make_preview_keyboard().as_markup(),
            )
            return True
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc).lower():
                logger.info("Preview message was not modified for user_id=%s", callback.from_user.id)
                return False
            raise

    async def remove_message_keyboard(callback: CallbackQuery) -> None:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc).lower():
                return
            logger.info("Could not remove keyboard for user_id=%s: %s", callback.from_user.id, exc)

    async def send_preview_message(target_message: Message, draft: DraftPost) -> None:
        await target_message.answer_photo(
            photo=draft.photo_file_id,
            caption=draft.build_preview_text(),
            reply_markup=make_preview_keyboard().as_markup(),
        )

    def parse_post_id(raw_value: str) -> UUID | None:
        try:
            return UUID(raw_value)
        except ValueError:
            return None

    async def load_user_draft_by_callback(
        callback: CallbackQuery,
        raw_post_id: str,
    ) -> tuple[UUID | None, DraftPost | None, str | None, bool]:
        callback_text: str | None = None
        show_alert = False

        if await reject_callback_if_not_allowed(callback, settings):
            return None, None, callback_text, show_alert

        post_id = parse_post_id(raw_post_id)
        if post_id is None:
            return None, None, "Не удалось распознать черновик.", True

        post = await services.draft_repository.get_user_draft(callback.from_user.id, post_id)
        if post is None:
            return None, None, "Черновик не найден или уже недоступен.", True

        return post_id, services.post_repository.build_draft_view(post), None, False

    async def load_post_for_callback(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> tuple[UUID | None, DraftPost | None, str | None, bool]:
        callback_text: str | None = None
        show_alert = False

        if await reject_callback_if_not_allowed(callback, settings):
            return None, None, callback_text, show_alert

        post_id, draft = await get_current_post(state)
        if not post_id:
            callback_text = "Текущий сценарий уже завершён или сброшен. Начните новый через /new."
            show_alert = True
            return None, None, callback_text, show_alert
        if not draft:
            callback_text = "Черновик не найден в базе. Начните новый сценарий через /new."
            show_alert = True
            return None, None, callback_text, show_alert

        return post_id, draft, callback_text, show_alert

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
            "Привет! Я бот Magnolia Verde для подготовки постов в Telegram-канал.\n\n"
            "Что я умею:\n"
            "• принять фото букета или цветка;\n"
            "• собрать черновик подписи;\n"
            "• показать предпросмотр;\n"
            "• сохранить черновик или опубликовать пост.\n\n"
            "Основные команды:\n"
            "/new — создать новый пост\n"
            "/drafts — посмотреть последние черновики\n"
            "/help — подсказка по командам\n"
            "/cancel — отменить текущий сценарий"
        )

    @router.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        await message.answer(
            "Подсказка по работе с ботом:\n\n"
            "/start — краткое описание и быстрый старт\n"
            "/new — начать новый сценарий и отправить фото\n"
            "/drafts — показать и открыть сохранённые черновики\n"
            "/cancel — отменить текущий сценарий\n\n"
            "После фото бот покажет предпросмотр, где можно:\n"
            "• перегенерировать подпись;\n"
            "• сократить текст;\n"
            "• сделать подпись более премиальной;\n"
            "• добавить цену, наличие и историю;\n"
            "• отредактировать текст вручную;\n"
            "• сохранить черновик или опубликовать пост."
        )

    @router.message(Command("new"))
    async def cmd_new(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        logger.info("Starting new post flow for user_id=%s", message.from_user.id)
        await state.clear()
        await state.set_state(DraftCreation.waiting_for_photo)
        await message.answer("Отправьте одно фото цветка или букета, и я соберу черновик поста.")

    @router.message(Command("drafts"))
    async def cmd_drafts(message: Message) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        drafts = await services.draft_repository.list_user_drafts(message.from_user.id)
        if not drafts:
            await message.answer(
                "Сохранённых черновиков пока нет.\n"
                "Начните новый сценарий через /new и сохраните пост кнопкой «Сохранить в черновики»."
            )
            return

        await message.answer("Последние черновики:")
        for draft in drafts:
            caption_preview = (draft.caption or "").strip().replace("\n", " ")
            if len(caption_preview) > 80:
                caption_preview = caption_preview[:77] + "..."
            status_title = draft.status.value
            header = f"Черновик #{draft.id}\nСтатус: {status_title}\nТип: {draft.object_type or 'композиция'}"
            text = header if not caption_preview else f"{header}\n\n{caption_preview}"

            photo_file_id = draft.source_photo_file_id or (
                draft.images[0].telegram_file_id if getattr(draft, "images", None) else None
            )
            if photo_file_id:
                await message.answer_photo(
                    photo=photo_file_id,
                    caption=text,
                    reply_markup=make_draft_actions_keyboard(str(draft.id)).as_markup(),
                )
            else:
                await message.answer(
                    text,
                    reply_markup=make_draft_actions_keyboard(str(draft.id)).as_markup(),
                )

    @router.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        await archive_current_post(state)
        await state.clear()
        logger.info("Current flow cancelled by user_id=%s", message.from_user.id)
        await message.answer("Сценарий отменён. Если нужно, начните заново через /new.")

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
        post_id, draft = await get_current_post(state)
        if not post_id or not draft:
            await state.clear()
            await message.answer("Не удалось найти текущий черновик. Начните заново через /new.")
            return
        draft.price_text = services.draft_factory.normalize_price(message.text)
        updated_post = await services.post_repository.update_post(post_id=post_id, draft=draft)
        if not updated_post:
            await state.clear()
            await message.answer("Не удалось обновить черновик. Начните заново через /new.")
            return
        await save_context_to_state(state, updated_post.id, draft)
        await state.set_state(None)
        logger.info("Updated price for user_id=%s", message.from_user.id)
        await message.answer("Цену добавил.")
        await send_preview_message(message, draft)

    @router.message(DraftCreation.waiting_for_availability, F.text)
    async def receive_availability(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        post_id, draft = await get_current_post(state)
        if not post_id or not draft:
            await state.clear()
            await message.answer("Не удалось найти текущий черновик. Начните заново через /new.")
            return
        draft.availability_text = services.draft_factory.normalize_availability(message.text)
        updated_post = await services.post_repository.update_post(post_id=post_id, draft=draft)
        if not updated_post:
            await state.clear()
            await message.answer("Не удалось обновить черновик. Начните заново через /new.")
            return
        await save_context_to_state(state, updated_post.id, draft)
        await state.set_state(None)
        logger.info("Updated availability for user_id=%s", message.from_user.id)
        await message.answer("Наличие обновил.")
        await send_preview_message(message, draft)

    @router.message(DraftCreation.waiting_for_manual_caption, F.text)
    async def receive_manual_caption(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        post_id, draft = await get_current_post(state)
        if not post_id or not draft:
            await state.clear()
            await message.answer("Не удалось найти текущий черновик. Начните заново через /new.")
            return
        draft.caption = message.text.strip()
        updated_post = await services.post_repository.update_post(
            post_id=post_id,
            draft=draft,
            status=PostStatus.ready,
        )
        if not updated_post:
            await state.clear()
            await message.answer("Не удалось обновить черновик. Начните заново через /new.")
            return
        await save_context_to_state(state, updated_post.id, draft)
        await state.set_state(None)
        logger.info("Updated caption manually for user_id=%s", message.from_user.id)
        await message.answer("Текст обновил.")
        await send_preview_message(message, draft)

    @router.callback_query(F.data == "shorten")
    async def cb_shorten(callback: CallbackQuery, state: FSMContext) -> None:
        callback_text = "Сократил"
        show_alert = False

        try:
            post_id, draft, callback_text_override, show_alert_override = await load_post_for_callback(callback, state)
            if callback_text_override:
                callback_text = callback_text_override
                show_alert = show_alert_override
                return

            assert post_id is not None and draft is not None
            shortened_caption = services.caption.shorten_caption(draft.caption)
            if shortened_caption == draft.caption:
                callback_text = "Подпись уже достаточно короткая."
                return

            draft.caption = shortened_caption
            updated_post = await services.post_repository.update_post(
                post_id=post_id,
                draft=draft,
                status=PostStatus.ready,
            )
            if not updated_post:
                callback_text = "Не удалось обновить черновик. Попробуйте ещё раз."
                show_alert = True
                return

            await save_context_to_state(state, updated_post.id, draft)
            preview_updated = await update_preview(callback, draft)
            if not preview_updated:
                callback_text = "Подпись уже выглядит коротко, предпросмотр не изменился."
            logger.info("Shortened caption for user_id=%s post_id=%s", callback.from_user.id, post_id)
        except Exception:
            logger.exception("Caption shortening failed for user_id=%s", callback.from_user.id)
            callback_text = "Не удалось сократить подпись. Попробуйте ещё раз."
            show_alert = True
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data == "regenerate")
    async def cb_regenerate(callback: CallbackQuery, state: FSMContext) -> None:
        callback_text = "Перегенерировал"
        show_alert = False

        try:
            post_id, draft, callback_text_override, show_alert_override = await load_post_for_callback(callback, state)
            if callback_text_override:
                callback_text = callback_text_override
                show_alert = show_alert_override
                return

            assert post_id is not None and draft is not None
            current_caption = draft.caption
            regenerated_caption = services.caption.regenerate_caption(
                draft.to_analysis(),
                current_caption=current_caption,
            )
            if not regenerated_caption:
                callback_text = "Сейчас не удалось перегенерировать подпись для этого поста."
                show_alert = True
                logger.warning("Caption regeneration unavailable for post_id=%s", post_id)
                return

            if regenerated_caption == current_caption:
                callback_text = "Не удалось подобрать новый вариант подписи. Попробуйте ещё раз позже."
                show_alert = True
                logger.info("Caption regeneration returned same text for post_id=%s", post_id)
                return

            draft.caption = regenerated_caption
            updated_post = await services.post_repository.update_post(
                post_id=post_id,
                draft=draft,
                status=PostStatus.ready,
            )
            if not updated_post:
                callback_text = "Не удалось обновить черновик. Попробуйте ещё раз."
                show_alert = True
                return

            await save_context_to_state(state, updated_post.id, draft)
            preview_updated = await update_preview(callback, draft)
            if not preview_updated:
                callback_text = "Подпись уже актуальна, новый вариант не потребовался."
            logger.info("Regenerated caption for user_id=%s post_id=%s", callback.from_user.id, post_id)
        except Exception:
            logger.exception("Caption regeneration failed for user_id=%s", callback.from_user.id)
            callback_text = "Не удалось перегенерировать подпись. Попробуйте ещё раз."
            show_alert = True
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data == "premium")
    async def cb_premium(callback: CallbackQuery, state: FSMContext) -> None:
        callback_text = "Сделал премиальнее"
        show_alert = False

        try:
            post_id, draft, callback_text_override, show_alert_override = await load_post_for_callback(callback, state)
            if callback_text_override:
                callback_text = callback_text_override
                show_alert = show_alert_override
                return

            assert post_id is not None and draft is not None
            premium_caption = services.caption.generate_caption(draft.to_analysis(), premium=True)
            if premium_caption == draft.caption:
                callback_text = "Подпись уже выглядит достаточно выразительно."
                return

            draft.caption = premium_caption
            updated_post = await services.post_repository.update_post(
                post_id=post_id,
                draft=draft,
                status=PostStatus.ready,
            )
            if not updated_post:
                callback_text = "Не удалось обновить черновик. Попробуйте ещё раз."
                show_alert = True
                return

            await save_context_to_state(state, updated_post.id, draft)
            preview_updated = await update_preview(callback, draft)
            if not preview_updated:
                callback_text = "Подпись уже актуальна, предпросмотр не изменился."
            logger.info("Premium caption generated for user_id=%s post_id=%s", callback.from_user.id, post_id)
        except Exception:
            logger.exception("Premium caption generation failed for user_id=%s", callback.from_user.id)
            callback_text = "Не удалось сделать подпись более премиальной. Попробуйте ещё раз."
            show_alert = True
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data == "add_price")
    async def cb_add_price(callback: CallbackQuery, state: FSMContext) -> None:
        callback_text = ""
        show_alert = False
        try:
            post_id, draft, callback_text_override, show_alert_override = await load_post_for_callback(callback, state)
            if callback_text_override:
                callback_text = callback_text_override
                show_alert = show_alert_override
                return
            assert post_id is not None and draft is not None
            await save_context_to_state(state, post_id, draft)
            await state.set_state(DraftCreation.waiting_for_price)
            await callback.message.reply("Отправьте цену, например: 4500")
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data == "add_availability")
    async def cb_add_availability(callback: CallbackQuery, state: FSMContext) -> None:
        callback_text = ""
        show_alert = False
        try:
            post_id, draft, callback_text_override, show_alert_override = await load_post_for_callback(callback, state)
            if callback_text_override:
                callback_text = callback_text_override
                show_alert = show_alert_override
                return
            assert post_id is not None and draft is not None
            await save_context_to_state(state, post_id, draft)
            await state.set_state(DraftCreation.waiting_for_availability)
            await callback.message.reply(
                "Отправьте наличие, например: В наличии, Под заказ или Ограниченное количество."
            )
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data == "add_story")
    async def cb_add_story(callback: CallbackQuery, state: FSMContext) -> None:
        callback_text = "Историю добавил"
        show_alert = False

        try:
            post_id, draft, callback_text_override, show_alert_override = await load_post_for_callback(callback, state)
            if callback_text_override:
                callback_text = callback_text_override
                show_alert = show_alert_override
                return
            assert post_id is not None and draft is not None

            story_text = services.caption.build_story(draft.to_analysis())
            if not story_text:
                callback_text = "Не удалось уверенно определить историю цветка."
                show_alert = True
                return
            if story_text == draft.story_text:
                callback_text = "История уже добавлена."
                return

            draft.story_text = story_text
            updated_post = await services.post_repository.update_post(
                post_id=post_id,
                draft=draft,
                status=PostStatus.ready,
            )
            if not updated_post:
                callback_text = "Не удалось обновить черновик. Попробуйте ещё раз."
                show_alert = True
                return

            await save_context_to_state(state, updated_post.id, draft)
            preview_updated = await update_preview(callback, draft)
            if not preview_updated:
                callback_text = "История уже актуальна, предпросмотр не изменился."
            logger.info("Added story for user_id=%s post_id=%s", callback.from_user.id, post_id)
        except Exception:
            logger.exception("Story generation failed for user_id=%s", callback.from_user.id)
            callback_text = "Не удалось добавить историю. Попробуйте ещё раз."
            show_alert = True
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data == "edit_caption")
    async def cb_edit_caption(callback: CallbackQuery, state: FSMContext) -> None:
        callback_text = ""
        show_alert = False
        try:
            post_id, draft, callback_text_override, show_alert_override = await load_post_for_callback(callback, state)
            if callback_text_override:
                callback_text = callback_text_override
                show_alert = show_alert_override
                return
            assert post_id is not None and draft is not None
            await save_context_to_state(state, post_id, draft)
            await state.set_state(DraftCreation.waiting_for_manual_caption)
            await callback.message.reply("Отправьте новый текст подписи целиком.")
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data == "save_draft")
    async def cb_save_draft(callback: CallbackQuery, state: FSMContext) -> None:
        callback_text = "Черновик сохранён"
        show_alert = False

        try:
            post_id, draft, callback_text_override, show_alert_override = await load_post_for_callback(callback, state)
            if callback_text_override:
                callback_text = callback_text_override
                show_alert = show_alert_override
                return
            assert post_id is not None and draft is not None

            updated_post = await services.post_repository.update_post(
                post_id=post_id,
                draft=draft,
                status=PostStatus.draft,
            )
            if not updated_post:
                callback_text = "Не удалось сохранить черновик. Попробуйте ещё раз."
                show_alert = True
                return

            await state.clear()
            logger.info("Saved draft post_id=%s for user_id=%s", post_id, callback.from_user.id)
            await callback.message.reply(f"Черновик сохранён в PostgreSQL с id {post_id}.")
        except Exception:
            logger.exception("Draft save failed for user_id=%s", callback.from_user.id)
            callback_text = "Не удалось сохранить черновик. Попробуйте ещё раз."
            show_alert = True
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data == "publish")
    async def cb_publish(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
        callback_text = "Опубликовано"
        show_alert = False

        try:
            post_id, draft, callback_text_override, show_alert_override = await load_post_for_callback(callback, state)
            if callback_text_override:
                callback_text = callback_text_override
                show_alert = show_alert_override
                return
            assert post_id is not None and draft is not None

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
            await callback.message.reply("Готово: пост отправлен в канал.")
        except Exception as exc:
            logger.exception("Publish failed for user_id=%s", callback.from_user.id)
            post_id = await get_post_id(state)
            if post_id:
                await services.post_repository.mark_failed(post_id, str(exc))
            callback_text = "Не удалось опубликовать пост в канал. Черновик сохранён со статусом ошибки."
            show_alert = True
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data.startswith("draft_open:"))
    async def cb_open_draft(callback: CallbackQuery, state: FSMContext) -> None:
        callback_text = "Черновик открыт"
        show_alert = False

        try:
            raw_post_id = callback.data.split(":", 1)[1]
            post_id, draft, callback_text_override, show_alert_override = await load_user_draft_by_callback(
                callback,
                raw_post_id,
            )
            if callback_text_override:
                callback_text = callback_text_override
                show_alert = show_alert_override
                return

            assert post_id is not None and draft is not None
            await save_context_to_state(state, post_id, draft)
            await state.set_state(None)
            await callback.message.reply("Открыл черновик для редактирования.")
            await send_preview_message(callback.message, draft)
            logger.info("Opened draft post_id=%s for user_id=%s", post_id, callback.from_user.id)
        except Exception:
            logger.exception("Open draft failed for user_id=%s", callback.from_user.id)
            callback_text = "Не удалось открыть черновик."
            show_alert = True
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data.startswith("draft_publish:"))
    async def cb_publish_draft(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
        callback_text = "Опубликовано"
        show_alert = False

        try:
            raw_post_id = callback.data.split(":", 1)[1]
            post_id, draft, callback_text_override, show_alert_override = await load_user_draft_by_callback(
                callback,
                raw_post_id,
            )
            if callback_text_override:
                callback_text = callback_text_override
                show_alert = show_alert_override
                return

            assert post_id is not None and draft is not None
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
            current_post_id = await get_post_id(state)
            if current_post_id == post_id:
                await state.clear()
            await remove_message_keyboard(callback)
            await callback.message.reply("Черновик опубликован в канал.")
            logger.info("Published draft from drafts list post_id=%s user_id=%s", post_id, callback.from_user.id)
        except Exception as exc:
            logger.exception("Publish draft failed for user_id=%s", callback.from_user.id)
            post_id = parse_post_id(callback.data.split(":", 1)[1])
            if post_id:
                await services.post_repository.mark_failed(post_id, str(exc))
            callback_text = "Не удалось опубликовать черновик. Он сохранён со статусом ошибки."
            show_alert = True
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data.startswith("draft_delete:"))
    async def cb_delete_draft(callback: CallbackQuery, state: FSMContext) -> None:
        callback_text = "Черновик удалён"
        show_alert = False

        try:
            raw_post_id = callback.data.split(":", 1)[1]
            post_id = parse_post_id(raw_post_id)
            if post_id is None:
                callback_text = "Не удалось распознать черновик."
                show_alert = True
                return

            archived_post = await services.draft_repository.archive_user_draft(callback.from_user.id, post_id)
            if archived_post is None:
                callback_text = "Черновик не найден или уже удалён."
                show_alert = True
                return

            current_post_id = await get_post_id(state)
            if current_post_id == post_id:
                await state.clear()
            await remove_message_keyboard(callback)
            await callback.message.reply("Черновик убран из активного списка.")
            logger.info("Archived draft post_id=%s for user_id=%s", post_id, callback.from_user.id)
        except Exception:
            logger.exception("Delete draft failed for user_id=%s", callback.from_user.id)
            callback_text = "Не удалось удалить черновик."
            show_alert = True
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.callback_query(F.data == "cancel")
    async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
        callback_text = "Отменено"
        show_alert = False
        try:
            if await reject_callback_if_not_allowed(callback, settings):
                return
            await archive_current_post(state)
            await state.clear()
            logger.info("Cancelled current flow by user_id=%s", callback.from_user.id)
            await callback.message.reply("Сценарий отменён. Можно начать заново через /new.")
        finally:
            await callback.answer(callback_text, show_alert=show_alert)

    @router.message(DraftCreation.waiting_for_photo)
    async def waiting_for_photo_fallback(message: Message) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        await message.answer("Сейчас нужен именно снимок. Отправьте фото цветка или букета, либо используйте /cancel.")

    @router.message()
    async def fallback_message(message: Message, state: FSMContext) -> None:
        if await reject_message_if_not_allowed(message, settings):
            return
        current_state = await state.get_state()
        if current_state == DraftCreation.waiting_for_price.state:
            await message.answer("Сейчас жду цену. Отправьте сумму сообщением или используйте /cancel.")
            return
        if current_state == DraftCreation.waiting_for_availability.state:
            await message.answer("Сейчас жду наличие. Отправьте текст сообщением или используйте /cancel.")
            return
        if current_state == DraftCreation.waiting_for_manual_caption.state:
            await message.answer("Сейчас жду новый текст подписи. Отправьте сообщение целиком или используйте /cancel.")
            return
        await message.answer(
            "Не удалось понять сообщение.\n"
            "Используйте /new для нового поста, /drafts для списка черновиков или /help для подсказки."
        )

    return router
