from aiogram.fsm.state import State, StatesGroup


class SubscriptionState(StatesGroup):
    choosing_period = State()


class RenewalState(StatesGroup):
    choosing_period = State()


class ChangeTariffState(StatesGroup):
    choosing_tariff = State()
    choosing_period = State()