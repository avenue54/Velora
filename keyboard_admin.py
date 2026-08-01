from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ======================
# ГЛАВНОЕ МЕНЮ АДМИНКИ
# ======================

def admin_main_keyboard():

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📊 Статистика"
                )
            ],
            [
                KeyboardButton(
                    text="👥 Пользователи"
                ),
                KeyboardButton(
                    text="💳 Подписки"
                )
            ],
            [
                KeyboardButton(
                    text="📢 Рассылка"
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


# ======================
# КНОПКИ УПРАВЛЕНИЯ ПОДПИСКОЙ
# ======================

def subscription_admin_keyboard(subscription_id):

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Активировать",
        callback_data=f"activate:{subscription_id}"
    )

    builder.button(
        text="❌ Отклонить",
        callback_data=f"reject:{subscription_id}"
    )

    builder.adjust(1)

    return builder.as_markup()


def broadcast_cancel_keyboard():

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="❌ Отмена рассылки")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard
