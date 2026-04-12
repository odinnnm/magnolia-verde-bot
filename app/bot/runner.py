import logging

from app.bot.app import create_bot, create_dispatcher
from app.db.session import DatabaseManager
from app.services.container import build_service_container
from app.utils.config import get_settings
from app.utils.logging import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    logger.info("Starting Magnolia Verde bot")

    db = DatabaseManager(settings)
    services = build_service_container(db)
    bot = create_bot(settings)
    dispatcher = create_dispatcher(settings, services)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await dispatcher.storage.close()
        await db.dispose()
