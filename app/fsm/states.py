from aiogram.fsm.state import State, StatesGroup


class DraftCreation(StatesGroup):
    waiting_for_photo = State()
    analyzing_photo = State()
    waiting_for_price = State()
    waiting_for_manual_caption = State()
