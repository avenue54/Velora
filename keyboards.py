from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Подключиться")],
            [
                KeyboardButton(text="👤 Мой аккаунт"),
                KeyboardButton(text="💳 Тарифы"),
            ],
            [
                KeyboardButton(text="🌍 Серверы"),
                KeyboardButton(text="📖 Инструкция"),
            ],
            [
                KeyboardButton(text="💬 Поддержка"),
                KeyboardButton(text="🛡️ О VPN"),
            ],
        ],
        resize_keyboard=True,
    )


def tariffs_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🟢 Start"),
                KeyboardButton(text="🔵 Plus ⭐"),
                KeyboardButton(text="🟣 Pro"),
            ],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )


def after_price_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Изменить тариф")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )


def connect_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Выбрать тариф")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )


def guide_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📱 iPhone / iPad"),
                KeyboardButton(text="🤖 Android"),
            ],
            [
                KeyboardButton(text="💻 Windows"),
                KeyboardButton(text="🍎 macOS"),
            ],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )


def platform_ios_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Получить конфигурацию")],
            [KeyboardButton(text="💬 Написать в поддержку")],
            [
                KeyboardButton(text="⬅️ К выбору платформы"),
                KeyboardButton(text="🏠 Главное меню"),
            ],
        ],
        resize_keyboard=True,
    )


def platform_android_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Получить конфигурацию")],
            [KeyboardButton(text="💬 Написать в поддержку")],
            [
                KeyboardButton(text="⬅️ К выбору платформы"),
                KeyboardButton(text="🏠 Главное меню"),
            ],
        ],
        resize_keyboard=True,
    )


def platform_windows_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Получить конфигурацию")],
            [KeyboardButton(text="🌍 Выбрать сервер")],
            [KeyboardButton(text="💬 Написать в поддержку")],
            [
                KeyboardButton(text="⬅️ К выбору платформы"),
                KeyboardButton(text="🏠 Главное меню"),
            ],
        ],
        resize_keyboard=True,
    )


def platform_macos_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Получить конфигурацию")],
            [KeyboardButton(text="💬 Написать в поддержку")],
            [
                KeyboardButton(text="⬅️ К выбору платформы"),
                KeyboardButton(text="🏠 Главное меню"),
            ],
        ],
        resize_keyboard=True,
    )


def get_config_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Выбрать тариф")],
            [KeyboardButton(text="👤 Мой аккаунт")],
            [
                KeyboardButton(text="⬅️ Назад"),
                KeyboardButton(text="🏠 Главное меню"),
            ],
        ],
        resize_keyboard=True,
    )


def guide_support_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Написать в поддержку")],
            [
                KeyboardButton(text="⬅️ Назад"),
                KeyboardButton(text="🏠 Главное меню"),
            ],
        ],
        resize_keyboard=True,
    )


def plans_keyboard(plans) -> ReplyKeyboardMarkup:
    keyboard = []
    added = set()
    for plan in plans:
        name = plan[1]
        if name not in added:
            label = {
                "Start": "🟢 Start",
                "Plus": "🔵 Plus ⭐",
                "Pro": "🟣 Pro",
            }.get(name, name)
            keyboard.append([KeyboardButton(text=label)])
            added.add(name)
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def period_keyboard(plans) -> ReplyKeyboardMarkup:
    keyboard = []
    for plan in plans:
        keyboard.append(
            [KeyboardButton(text=f"{plan[4]} — {plan[5]}")]
        )
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def support_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Написать в поддержку")],
            [KeyboardButton(text="🛡️ О VPN")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )


def contact_dev_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="👨‍💻 Связаться с поддержкой",
        url="https://t.me/Velora_Supports",
    )
    builder.adjust(1)
    return builder.as_markup()


def about_vpn_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 О VELORA")],
            [KeyboardButton(text="❓ Что такое VPN")],
            [KeyboardButton(text="🔐 Как работает защита")],
            [KeyboardButton(text="🛡️ Конфиденциальность")],
            [KeyboardButton(text="⚡ Производительность")],
            [KeyboardButton(text="🌍 Серверы VELORA")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )


def renewal_period_keyboard(plans) -> ReplyKeyboardMarkup:
    keyboard = []
    for plan in plans:
        keyboard.append(
            [KeyboardButton(text=f"🔄 {plan[4]} — {plan[5]}")]
        )
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    keyboard.append([KeyboardButton(text="🏠 Главное меню")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def change_tariff_keyboard(current_plan: str) -> ReplyKeyboardMarkup:
    all_plans = [
        ("🟢 Start", "Start"),
        ("🔵 Plus ⭐", "Plus"),
        ("🟣 Pro", "Pro"),
    ]
    keyboard = []
    for btn_text, plan_name in all_plans:
        if plan_name != current_plan:
            keyboard.append([KeyboardButton(text=btn_text)])
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    keyboard.append([KeyboardButton(text="🏠 Главное меню")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def devices_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Главное меню")]],
        resize_keyboard=True,
    )


def profile_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔄 Продлить подписку"),
                KeyboardButton(text="💳 Изменить тариф"),
            ],
            [KeyboardButton(text="⚙️ Устройства")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )


def channel_subscribe_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📢 Подписаться на канал",
        url="https://t.me/Velora_news",
    )
    builder.button(
        text="✅ Я подписался",
        callback_data="check_subscription",
    )
    builder.adjust(1)
    return builder.as_markup()
