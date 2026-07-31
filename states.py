from aiogram.fsm.state import State, StatesGroup


class SubscriptionState(StatesGroup):
    choosing_period = State()