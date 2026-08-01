from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import (
    get_all_users,
    get_statistics,
    get_subscriptions,
    update_subscription_status,
    activate_subscription,
    get_all_telegram_ids,
    get_subscription_user_telegram_id,
)
from keyboard_admin import (
    admin_main_keyboard,
    subscription_admin_keyboard,
    broadcast_cancel_keyboard,
)
from admin_texts import (
    ADMIN_PANEL_TEXT,
    STATISTICS_TEXT,
)
from config import ADMIN_ID
from states import BroadcastState

router = Router()


# ======================
# АДМИН ПАНЕЛЬ
# ======================

@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.clear()
    await message.answer(
        ADMIN_PANEL_TEXT,
        reply_markup=admin_main_keyboard(),
    )


@router.message(F.text == "👥 Пользователи")
async def users_list(message: Message):
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


@router.message(F.text == "💳 Подписки")
async def subscriptions_list(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    data = get_subscriptions()

    if not data:
        await message.answer("💳 Подписок пока нет")
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
            date,
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
            reply_markup=subscription_admin_keyboard(sub_id),
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
            pending=data["pending"],
        )
    )


# ======================
# РАССЫЛКА
# ======================

@router.message(F.text == "📢 Рассылка")
async def broadcast_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.set_state(BroadcastState.waiting_message)
    await message.answer(
        "📢 Рассылка\n\n"
        "Напишите сообщение, которое получат все пользователи бота.\n\n"
        "Поддерживается HTML-разметка.\n"
        "Для отмены нажмите «❌ Отмена рассылки».",
        reply_markup=broadcast_cancel_keyboard(),
    )


@router.message(F.text == "❌ Отмена рассылки")
async def broadcast_cancel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.clear()
    await message.answer(
        "❌ Рассылка отменена",
        reply_markup=admin_main_keyboard(),
    )


@router.message(BroadcastState.waiting_message)
async def broadcast_send(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text or message.caption
    if not text:
        await message.answer(
            "❌ Нужен текст сообщения. Попробуйте ещё раз или отмените рассылку."
        )
        return

    users = get_all_telegram_ids()
    total = len(users)
    success = 0
    fail = 0

    await message.answer(f"📤 Рассылка запущена...\nПолучателей: {total}")

    for tg_id in users:
        try:
            await message.bot.send_message(
                chat_id=tg_id,
                text=f"📢 <b>Сообщение от VELORA</b>\n\n{text}",
            )
            success += 1
        except Exception as e:
            print(f"Broadcast fail {tg_id}: {e}")
            fail += 1

    await state.clear()
    await message.answer(
        f"✅ Рассылка завершена\n\n"
        f"Успешно: {success}\n"
        f"Ошибок: {fail}\n"
        f"Всего: {total}",
        reply_markup=admin_main_keyboard(),
    )


# ======================
# АКТИВАЦИЯ / ОТКЛОНЕНИЕ
# ======================

@router.callback_query(F.data.startswith("activate:"))
async def activate_subscription_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    subscription_id = int(callback.data.split(":")[1])
    print("АКТИВАЦИЯ:", subscription_id)

    activate_subscription(subscription_id)

    user_tg_id = get_subscription_user_telegram_id(subscription_id)
    if user_tg_id:
        try:
            await callback.bot.send_message(
                chat_id=user_tg_id,
                text=(
                    "✅ <b>Подписка активирована!</b>\n\n"
                    f"Заявка #{subscription_id} подтверждена.\n"
                    "Доступ к VELORA открыт.\n\n"
                    "Перейдите в «👤 Мой аккаунт», чтобы посмотреть детали,\n"
                    "или в «📖 Инструкция» для подключения."
                ),
            )
        except Exception as e:
            print(f"Notify activate fail: {e}")

    await callback.message.delete()
    await callback.message.answer(
        f"✅ Подписка #{subscription_id} активирована"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reject:"))
async def reject_subscription_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    subscription_id = int(callback.data.split(":")[1])
    print("ОТКЛОНЕНИЕ:", subscription_id)

    update_subscription_status(subscription_id, "rejected")

    user_tg_id = get_subscription_user_telegram_id(subscription_id)
    if user_tg_id:
        try:
            await callback.bot.send_message(
                chat_id=user_tg_id,
                text=(
                    "❌ <b>Подписка не активирована</b>\n\n"
                    f"Заявка #{subscription_id} отклонена.\n\n"
                    "Если вы оплатили, напишите в поддержку — разберёмся."
                ),
            )
        except Exception as e:
            print(f"Notify reject fail: {e}")

    await callback.message.delete()
    await callback.message.answer(
        f"❌ Подписка #{subscription_id} отклонена"
    )
    await callback.answer()
