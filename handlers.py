from aiogram import Router, F
from datetime import datetime
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards import (
    main_menu_reply_keyboard,
    tariffs_reply_keyboard,
    after_price_keyboard,
    connect_keyboard,
    guide_keyboard,
    plans_keyboard,
    period_keyboard,
    profile_keyboard
)
from texts import (
    WELCOME_TEXT,
    CONNECT_TEXT,
    ACCOUNT_TEXT,
    SERVERS_TEXT,
    GUIDE_TEXT,
    TARIFFS_TEXT,
    START_TEXT,
    PLUS_TEXT,
    PRO_TEXT,
    BUY_TEXT,
    SUPPORT_TEXT,
    SETTINGS_TEXT,
    MAIN_MENU_TEXT
)
from database import (
    add_user,
    get_user,
    get_plans,
    get_plans_by_name,
    get_plan_by_period,
    create_subscription,
    get_user_subscription,
    get_profile
)

from aiogram.fsm.context import FSMContext
from states import SubscriptionState

from services import subscription_status_text

router = Router()


# ======================
# START
# ======================

@router.message(CommandStart())
async def start(message: Message):

    print("START НАЖАТ")

    add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    print("БАЗА ОК")

    print("ОТПРАВЛЯЮ СООБЩЕНИЕ")

    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu_reply_keyboard()
    )

# ======================
# ГЛАВНОЕ МЕНЮ
# ======================

@router.message(F.text == "🚀 Подключиться")
async def connect(message: Message):
    await message.answer(
        CONNECT_TEXT,
        reply_markup=connect_keyboard()
    )


@router.message(F.text == "💳 Выбрать тариф")
async def choose_tariff(message: Message):
    await message.answer(
        TARIFFS_TEXT,
        reply_markup=tariffs_reply_keyboard()
    )


@router.message(F.text == "👤 Мой аккаунт")
async def my_profile(message: Message):

    profile = get_profile(
        message.from_user.id
    )


    if not profile:

        await message.answer(
            "👤 Профиль VELORA\n\n"
            "❌ Данные не найдены",
            reply_markup=profile_keyboard()
        )

        return



    (
        telegram_id,
        first_name,
        created_at,
        plan,
        period,
        price,
        status,
        start_date,
        end_date,
        devices_used
    ) = profile



    days_left = ""


    if end_date:

        end = datetime.strptime(
            end_date,
            "%Y-%m-%d %H:%M:%S"
        )


        days = (
            end - datetime.now()
        ).days


        if days < 0:
            days = 0


        days_left = (
            f"\n⏳ Осталось: {days} дней"
        )



    if not plan:

        await message.answer(

            "👤 Профиль VELORA\n\n"

            f"🆔 Telegram ID:\n"
            f"{telegram_id}\n\n"

            f"📅 Регистрация:\n"
            f"{created_at}\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "💳 Подписка:\n"
            "🔴 Нет активной подписки",

            reply_markup=profile_keyboard()
        )

        return




    await message.answer(

        "👤 Профиль VELORA\n\n"

        f"🆔 Telegram ID:\n"
        f"{telegram_id}\n\n"

        f"📅 Регистрация:\n"
        f"{created_at}\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "📊 Твоя подписка:\n\n"

        f"📊 Статус: {subscription_status_text(status)}\n"

        f"💳 Тариф: {plan}\n"

        f"📅 Срок: {period}\n"

        f"💰 Стоимость: {price}\n"

        f"📱 Устройств: {devices_used}\n"

        f"{days_left}\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "🚀 VELORA — безопасное подключение",

        reply_markup=profile_keyboard()
    )

@router.message(F.text == "🌍 Серверы")
async def servers(message: Message):
    await message.answer(
        SERVERS_TEXT
    )


@router.message(F.text == "📖 Инструкция")
async def guide(message: Message):
    await message.answer(
        GUIDE_TEXT,
        reply_markup=guide_keyboard()
    )


@router.message(F.text == "💬 Поддержка")
async def support(message: Message):
    await message.answer(
        SUPPORT_TEXT
    )


@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message):
    await message.answer(
        SETTINGS_TEXT
    )


# ======================
# ТАРИФЫ
# ======================

@router.message(F.text == "💳 Тарифы")
async def tariffs(message: Message):

    plans = get_plans()


    await message.answer(
        "💳 Тарифы VELORA\n\n"
        "Выберите тариф:",
        reply_markup=plans_keyboard(plans)
    )


@router.message(F.text == "🟢 Start")
async def start_tariff(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        plan="Start"
    )


    await state.set_state(
        SubscriptionState.choosing_period
    )


    plans = get_plans_by_name("Start")


    await message.answer(
        START_TEXT,
        reply_markup=period_keyboard(plans)
    )


@router.message(F.text == "🔵 Plus ⭐")
async def plus_tariff(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        plan="Plus"
    )


    await state.set_state(
        SubscriptionState.choosing_period
    )


    plans = get_plans_by_name("Plus")


    await message.answer(
        PLUS_TEXT,
        reply_markup=period_keyboard(plans)
    )


@router.message(F.text == "🟣 Pro")
async def pro_tariff(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        plan="Pro"
    )


    await state.set_state(
        SubscriptionState.choosing_period
    )


    plans = get_plans_by_name("Pro")


    await message.answer(
        PRO_TEXT,
        reply_markup=period_keyboard(plans)
    )


# ======================
# ПОКУПКА
# ======================

@router.message(F.text.contains("месяц"))
async def buy_tariff(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    plan_name = data.get("plan")


    if not plan_name:
        await message.answer(
            "❌ Тариф не выбран"
        )
        return


    parts = message.text.split(" — ")

    if len(parts) != 2:
        await message.answer(
            "❌ Некорректный выбор тарифа"
        )
        return


    period = parts[0]
    price = parts[1]


    plan = get_plan_by_period(
        plan_name,
        period
    )


    if not plan:
        await message.answer(
            f"❌ Тариф не найден\n\n"
            f"Тариф: {plan_name}\n"
            f"Срок: {period}"
        )
        return


    create_subscription(
        telegram_id=message.from_user.id,
        plan=plan[1],
        period=plan[4],
        price=plan[5]
    )


    await message.answer(
        "✅ Заявка создана\n\n"
        f"💳 Тариф: {plan[1]}\n"
        f"📅 Срок: {plan[4]}\n"
        f"💰 Цена: {plan[5]}\n\n"
        "Статус: ожидание оплаты",
        reply_markup=after_price_keyboard()
    )


    await state.clear()
# ======================
# НАВИГАЦИЯ
# ======================

@router.message(F.text.in_({"⬅️ Назад", "⬅️ Изменить тариф"}))
async def back_to_tariffs(message: Message):
    await message.answer(
        TARIFFS_TEXT,
        reply_markup=tariffs_reply_keyboard()
    )


@router.message(F.text == "🏠 Главное меню")
async def main_menu(message: Message):
    await message.answer(
        MAIN_MENU_TEXT,
        reply_markup=main_menu_reply_keyboard()
    )