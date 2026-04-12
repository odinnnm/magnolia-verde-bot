from aiogram import Bot, Dispatcher

from app.bot.handlers import setup_router
from app.fsm.storage import create_fsm_storage
from app.services.container import ServiceContainer
from app.utils.config import Settings


def create_bot(settings: Settings) -> Bot:
    return Bot(token=settings.bot_token)


def create_dispatcher(settings: Settings, services: ServiceContainer) -> Dispatcher:
    dispatcher = Dispatcher(storage=create_fsm_storage(settings))
    dispatcher.include_router(setup_router(services, settings))
    return dispatcher
