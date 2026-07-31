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
            [KeyboardButton(text="💬 Поддержка"), KeyboardButton(text="⚙️ Настройки")],
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
            [KeyboardButton(text="📱 iPhone"), KeyboardButton(text="🤖 Android")],
            [KeyboardButton(text="💻 Windows"), KeyboardButton(text="🍎 macOS")],
            [KeyboardButton(text="🏠 Главное меню")],
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