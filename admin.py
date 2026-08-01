from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import (
    get_all_users,
    get_all_subscriptions,
    get_statistics,
    get_subscriptions,
    update_subscription_status,
    activate_subscription
)

from keyboard_admin import (
    admin_main_keyboard,
    subscription_admin_keyboard
)

from admin_texts import (
    ADMIN_PANEL_TEXT,
    USERS_LIST_TEXT,
    SUBSCRIPTIONS_LIST_TEXT,
    SUBSCRIPTION_ACTIVE_TEXT,
    SUBSCRIPTION_REJECT_TEXT,
    NO_ACCESS_TEXT,
    STATISTICS_TEXT,
    SUBSCRIPTIONS_TEXT
)
from config import ADMIN_ID

router = Router()






# ======================
# АДМИН ПАНЕЛЬ
# ======================

@router.message(Command("admin"))
async def admin_panel(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
    ADMIN_PANEL_TEXT,
    reply_markup=admin_main_keyboard()
)


# ======================
# ПОЛЬЗОВАТЕЛИ
# ======================

@router.message(
    F.text == "👥 Пользователи"
)
async def users(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    users = get_all_users()


    text = "👥 Пользователи:\n\n"


    for user in users:

        text += (
            f"ID: {user[0]}\n"
            f"TG: {user[1]}\n"
            f"Имя: {user[3]}\n"
            f"Статус: {user[4]}\n\n"
        )


    await message.answer(text)


# ======================
# ПОДПИСКИ
# ======================

@router.message(F.text == "💳 Подписки")
async def subscriptions(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    data = get_subscriptions()


    if not data:

        await message.answer(
            "💳 Подписок пока нет"
        )

        return


    for sub in data:

        (
            sub_id,
            name,
            telegram_id,
            plan,
            period,
            price,
            status,
            date
        ) = sub


        text = (
            f"💳 Заявка #{sub_id}\n\n"
            f"👤 Пользователь: {name}\n"
            f"🆔 Telegram ID: {telegram_id}\n\n"
            f"💳 Тариф: {plan}\n"
            f"📅 Срок: {period}\n"
            f"💰 Цена: {price}\n\n"
            f"📊 Статус: {status}\n"
            f"🕒 {date}"
        )


        await message.answer(
            text,
            reply_markup=subscription_admin_keyboard(sub_id)
        )

@router.message(F.text == "📊 Статистика")
async def statistics(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    data = get_statistics()

    await message.answer(
        STATISTICS_TEXT.format(
            users=data["users"],
            subscriptions=data["subscriptions"],
            active=data["active"],
            pending=data["pending"]
        )
    )
    
@router.callback_query(F.data.startswith("activate:"))
async def activate_subscription(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    subscription_id = int(
        callback.data.split(":")[1]
    )

    print("АКТИВАЦИЯ:", subscription_id)

    activate_subscription(subscription_id)

    await callback.message.delete()

    await callback.message.answer(
    f"✅ Подписка #{subscription_id} активирована"
    )

    await callback.answer()
    
@router.callback_query(F.data.startswith("reject:"))
async def reject_subscription(callback: CallbackQuery):
    
    if callback.from_user.id != ADMIN_ID:
            await callback.answer(
                "Нет доступа",
                show_alert=True
            )
            return

    subscription_id = int(
        callback.data.split(":")[1]
    )

    print("ОТКЛОНЕНИЕ:", subscription_id)

    update_subscription_status(
        subscription_id,
        "rejected"
    )

    await callback.message.delete()

    await callback.message.answer(
    f"❌ Подписка #{subscription_id} отклонена"
    )

    await callback.answer()