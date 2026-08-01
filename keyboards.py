from aiogram.types import *
from aiogram.utils.keyboard import InlineKeyboardBuilder



def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Подключиться", callback_data="menu:connect")
    builder.button(text="👤 Мой аккаунт", callback_data="menu:account")
    builder.button(text="💳 Тарифы", callback_data="menu:tariffs")
    builder.button(text="🌍 Серверы", callback_data="menu:servers")
    builder.button(text="📖 Инструкция", callback_data="menu:guide")
    builder.button(text="💬 Поддержка", callback_data="menu:support")
    builder.button(text="⚙️ Настройки", callback_data="menu:settings")
    builder.adjust(1)
    return builder.as_markup()

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Подключиться")],
            [KeyboardButton(text="👤 Мой аккаунт"), KeyboardButton(text="💳 Тарифы")],
            [KeyboardButton(text="🌍 Серверы"), KeyboardButton(text="📖 Инструкция")],
            [KeyboardButton(text="💬 Поддержка"), KeyboardButton(text="🛡️ О VPN")],
        ],
        resize_keyboard=True
    )
    return keyboard

def tariffs_reply_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🟢 Start"),
                KeyboardButton(text="🔵 Plus ⭐"),
                KeyboardButton(text="🟣 Pro")
            ],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard



def after_price_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Изменить тариф")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard

def connect_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Выбрать тариф")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard

def guide_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 iPhone / iPad"), KeyboardButton(text="🤖 Android")],
            [KeyboardButton(text="💻 Windows"), KeyboardButton(text="🍎 macOS")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard


def platform_ios_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Получить конфигурацию")],
            [KeyboardButton(text="💬 Написать в поддержку")],
            [KeyboardButton(text="⬅️ К выбору платформы"), KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard


def platform_android_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Получить конфигурацию")],
            [KeyboardButton(text="💬 Написать в поддержку")],
            [KeyboardButton(text="⬅️ К выбору платформы"), KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard


def platform_windows_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Получить конфигурацию")],
            [KeyboardButton(text="🌍 Выбрать сервер")],
            [KeyboardButton(text="💬 Написать в поддержку")],
            [KeyboardButton(text="⬅️ К выбору платформы"), KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard


def platform_macos_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Получить конфигурацию")],
            [KeyboardButton(text="💬 Написать в поддержку")],
            [KeyboardButton(text="⬅️ К выбору платформы"), KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard


def get_config_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Выбрать тариф")],
            [KeyboardButton(text="👤 Мой аккаунт")],
            [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard


def guide_support_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Написать в поддержку")],
            [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard

def back_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard




def plans_keyboard(plans):

    keyboard = []

    added = set()


    for plan in plans:

        name = plan[1]


        if name not in added:

            keyboard.append(
                [
                    KeyboardButton(
                        text=(
                            "🟢 Start"
                            if name == "Start"
                            else
                            "🔵 Plus ⭐"
                            if name == "Plus"
                            else
                            "🟣 Pro"
                        )
                    )
                ]
            )

            added.add(name)


    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

def period_keyboard(plans):

    keyboard = []

    for plan in plans:
        keyboard.append(
            [
                KeyboardButton(
                    text=f"{plan[4]} — {plan[5]}"
                )
            ]
        )

    keyboard.append(
        [
            KeyboardButton(text="⬅️ Назад")
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )
    
    
def support_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Написать в поддержку")],
            [KeyboardButton(text="🛡️ О VPN")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard


def contact_dev_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="👨‍💻 Связаться с поддержкой",
        url="https://t.me/Velora_Supports"
    )
    builder.adjust(1)
    return builder.as_markup()


def about_vpn_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 О VELORA")],
            [KeyboardButton(text="❓ Что такое VPN")],
            [KeyboardButton(text="🔐 Как работает защита")],
            [KeyboardButton(text="🛡️ Конфиденциальность")],
            [KeyboardButton(text="⚡ Производительность")],
            [KeyboardButton(text="🌍 Серверы VELORA")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard


def renewal_period_keyboard(plans) -> ReplyKeyboardMarkup:
    keyboard = []
    for plan in plans:
        keyboard.append([KeyboardButton(text=f"🔄 {plan[4]} — {plan[5]}")])
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
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    return keyboard


def profile_keyboard() -> ReplyKeyboardMarkup:

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🔄 Продлить подписку"
                ),
                KeyboardButton(
                    text="💳 Изменить тариф"
                )
            ],
            [
                KeyboardButton(
                    text="⚙️ Устройства"
                )
            ],
            [
                KeyboardButton(
                    text="🏠 Главное меню"
                )
            ]
        ],
        resize_keyboard=True
    )

    return keyboard


def payment_pay_keyboard() -> InlineKeyboardMarkup:
    """Кнопка «Оплатить» — под сообщением заказа."""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить", callback_data="payment:pay")
    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard() -> ReplyKeyboardMarkup:
    """Кнопки внизу чата: проверить, изменить тариф, меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Проверить оплату")],
            [KeyboardButton(text="⬅️ Изменить тариф")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )
