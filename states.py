from aiogram.fsm.state import State, StatesGroup


class SubscriptionState(StatesGroup):
    choosing_period = State()


class RenewalState(StatesGroup):
    choosing_period = State()


class ChangeTariffState(StatesGroup):
    choosing_tariff = State()
    choosing_period = State()


class BroadcastState(StatesGroup):
    waiting_message = State()


class AdminAuthState(StatesGroup):
    waiting_password = State()
    waiting_name = State()
    waiting_new_password = State()


class PromoAdminState(StatesGroup):
    waiting_code = State()
    waiting_discount = State()
    waiting_bonus_days = State()
    waiting_max_uses = State()


class DeviceState(StatesGroup):
    waiting_label = State()


class PromoUserState(StatesGroup):
    waiting_code = State()
