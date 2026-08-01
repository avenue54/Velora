from aiogram import Router, F
from datetime import datetime
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from keyboards import (
    main_menu_reply_keyboard,
    tariffs_reply_keyboard,
    after_price_keyboard,
    connect_keyboard,
    guide_keyboard,
    plans_keyboard,
    period_keyboard,
    profile_keyboard,
    about_vpn_keyboard,
    support_keyboard,
    contact_dev_keyboard,
    renewal_period_keyboard,
    change_tariff_keyboard,
    devices_keyboard,
    platform_ios_keyboard,
    platform_android_keyboard,
    platform_windows_keyboard,
    platform_macos_keyboard,
    get_config_keyboard,
    guide_support_keyboard,
    payment_keyboard,
    payment_pay_keyboard,
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
    MAIN_MENU_TEXT,
    ABOUT_VPN_TEXT,
    ABOUT_VELORA_TEXT,
    WHAT_IS_VPN_TEXT,
    HOW_VPN_WORKS_TEXT,
    PRIVACY_TEXT,
    PERFORMANCE_TEXT,
    SERVERS_INFO_TEXT,
    SUPPORT_MAIN_TEXT,
    CONTACT_DEV_TEXT,
    GUIDE_IPHONE_TEXT,
    GUIDE_ANDROID_TEXT,
    GUIDE_WINDOWS_TEXT,
    GUIDE_MACOS_TEXT,
    GET_CONFIG_TEXT,
    GUIDE_SUPPORT_TEXT
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
from states import SubscriptionState, RenewalState, ChangeTariffState

from services import (
    subscription_status_text,
    create_order,
    get_order_screen_text,
    payment_pay_stub_text,
    payment_check_stub_text,
)

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
    expiry_str = ""

    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        days = (end - datetime.now()).days
        if days < 0:
            days = 0
        expiry_str = end.strftime("%d.%m.%y в %H:%M МСК")

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

    expiry_line = f"\nИстекает {expiry_str}" if status == "active" and expiry_str else ""

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
        f"📱 Устройств: {devices_used or 0}"
        f"{expiry_line}\n\n"
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


@router.message(F.text == "📱 iPhone / iPad")
async def guide_iphone(message: Message):
    await message.answer(
        GUIDE_IPHONE_TEXT,
        reply_markup=platform_ios_keyboard()
    )


@router.message(F.text == "🤖 Android")
async def guide_android(message: Message):
    await message.answer(
        GUIDE_ANDROID_TEXT,
        reply_markup=platform_android_keyboard()
    )


@router.message(F.text == "💻 Windows")
async def guide_windows(message: Message):
    await message.answer(
        GUIDE_WINDOWS_TEXT,
        reply_markup=platform_windows_keyboard()
    )


@router.message(F.text == "🍎 macOS")
async def guide_macos(message: Message):
    await message.answer(
        GUIDE_MACOS_TEXT,
        reply_markup=platform_macos_keyboard()
    )


@router.message(F.text == "📥 Получить конфигурацию")
async def get_config(message: Message):
    await message.answer(
        GET_CONFIG_TEXT,
        reply_markup=get_config_keyboard()
    )


@router.message(F.text == "💬 Поддержка по настройке")
async def guide_support(message: Message):
    await message.answer(
        GUIDE_SUPPORT_TEXT,
        reply_markup=guide_support_keyboard()
    )


@router.message(F.text == "💬 Поддержка")
async def support(message: Message):
    await message.answer(
        SUPPORT_MAIN_TEXT,
        reply_markup=support_keyboard()
    )

@router.message(F.text == "💬 Написать в поддержку")
async def contact_support(message: Message):
    await message.answer(
        CONTACT_DEV_TEXT,
        reply_markup=contact_dev_keyboard()
    )


@router.message(F.text == "🛡️ О VPN")
async def about_vpn(message: Message):
    await message.answer(
        ABOUT_VPN_TEXT,
        reply_markup=about_vpn_keyboard()
    )

@router.message(F.text == "🚀 О VELORA")
async def about_velora(message: Message):
    await message.answer(
        ABOUT_VELORA_TEXT,
        reply_markup=about_vpn_keyboard()
    )

@router.message(F.text == "❓ Что такое VPN")
async def what_is_vpn(message: Message):
    await message.answer(
        WHAT_IS_VPN_TEXT,
        reply_markup=about_vpn_keyboard()
    )

@router.message(F.text == "🔐 Как работает защита")
async def how_vpn_works(message: Message):
    await message.answer(
        HOW_VPN_WORKS_TEXT,
        reply_markup=about_vpn_keyboard()
    )

@router.message(F.text == "🛡️ Конфиденциальность")
async def privacy(message: Message):
    await message.answer(
        PRIVACY_TEXT,
        reply_markup=about_vpn_keyboard()
    )

@router.message(F.text == "⚡ Производительность")
async def performance(message: Message):
    await message.answer(
        PERFORMANCE_TEXT,
        reply_markup=about_vpn_keyboard()
    )

@router.message(F.text == "🌍 Серверы VELORA")
async def servers_info(message: Message):
    await message.answer(
        SERVERS_INFO_TEXT,
        reply_markup=about_vpn_keyboard()
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

@router.message(SubscriptionState.choosing_period, F.text.contains("месяц"))
async def buy_tariff(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()
    plan_name = data.get("plan")

    if not plan_name:
        await message.answer("❌ Тариф не выбран")
        return

    parts = message.text.split(" — ")
    if len(parts) != 2:
        await message.answer("❌ Некорректный выбор тарифа")
        return

    period = parts[0]
    price = parts[1]

    plan = get_plan_by_period(plan_name, period)
    if not plan:
        await message.answer(
            f"❌ Тариф не найден\n\n"
            f"Тариф: {plan_name}\n"
            f"Срок: {period}"
        )
        return

    # Не создаём подписку — только платёж (заказ)
    payment_id = create_order(
        telegram_id=message.from_user.id,
        plan=plan[1],
        period=plan[4],
        amount=plan[5],
    )

    await state.clear()

    await message.answer(
        get_order_screen_text(
            plan=plan[1],
            period=plan[4],
            amount=plan[5],
            status="pending",
        ),
        reply_markup=payment_pay_keyboard(),
    )
    await message.answer(
        "Доступные действия 👇",
        reply_markup=payment_keyboard(),
    )


# ======================
# ПРОДЛЕНИЕ ПОДПИСКИ
# ======================

@router.message(F.text == "🔄 Продлить подписку")
async def renew_subscription(message: Message, state: FSMContext):
    profile = get_profile(message.from_user.id)

    if not profile or not profile[3] or profile[6] != "active":
        await message.answer(
            "❌ У вас нет активной подписки для продления.\n\n"
            "Перейдите в раздел 💳 Тарифы для оформления.",
            reply_markup=profile_keyboard()
        )
        return

    plan = profile[3]
    end_date = profile[8]
    days_left = 0

    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        days_left = max(0, (end - datetime.now()).days)

    plans = get_plans_by_name(plan)

    await state.update_data(plan=plan)
    await state.set_state(RenewalState.choosing_period)

    await message.answer(
        f"🔄 Продление подписки\n\n"
        f"Ваша текущая подписка:\n\n"
        f"💳 Тариф: {plan}\n"
        f"📅 Осталось: {days_left} дней\n\n"
        f"Выберите срок продления:",
        reply_markup=renewal_period_keyboard(plans)
    )


@router.message(RenewalState.choosing_period, F.text.startswith("🔄"))
async def renewal_period_chosen(message: Message, state: FSMContext):
    data = await state.get_data()
    plan_name = data.get("plan")

    text = message.text.replace("🔄 ", "", 1)
    parts = text.split(" — ")
    if len(parts) != 2:
        await message.answer("❌ Некорректный выбор. Попробуйте снова.")
        return

    period, price = parts[0], parts[1]

    create_order(
        telegram_id=message.from_user.id,
        plan=plan_name,
        period=period,
        amount=price,
    )

    await state.clear()

    await message.answer(
        get_order_screen_text(
            plan=plan_name,
            period=period,
            amount=price,
            status="pending",
        ),
        reply_markup=payment_pay_keyboard(),
    )
    await message.answer(
        "Доступные действия 👇",
        reply_markup=payment_keyboard(),
    )


# ======================
# ИЗМЕНЕНИЕ ТАРИФА
# ======================

@router.message(F.text == "💳 Изменить тариф")
async def change_tariff(message: Message, state: FSMContext):
    profile = get_profile(message.from_user.id)

    if not profile or not profile[3]:
        await message.answer(
            "❌ У вас нет активной подписки.\n\n"
            "Перейдите в раздел 💳 Тарифы для оформления.",
            reply_markup=profile_keyboard()
        )
        return

    current_plan = profile[3]

    await state.update_data(current_plan=current_plan)
    await state.set_state(ChangeTariffState.choosing_tariff)

    plan_emoji = {"Start": "🟢", "Plus": "🔵", "Pro": "🟣"}
    emoji = plan_emoji.get(current_plan, "")

    await message.answer(
        f"💳 Изменение тарифа\n\n"
        f"Текущий тариф:\n"
        f"{emoji} {current_plan}\n\n"
        f"Выберите новый тариф:",
        reply_markup=change_tariff_keyboard(current_plan)
    )


@router.message(ChangeTariffState.choosing_tariff, F.text.in_({"🟢 Start", "🔵 Plus ⭐", "🟣 Pro"}))
async def new_tariff_chosen(message: Message, state: FSMContext):
    data = await state.get_data()
    current_plan = data.get("current_plan")

    name_map = {"🟢 Start": "Start", "🔵 Plus ⭐": "Plus", "🟣 Pro": "Pro"}
    new_plan = name_map[message.text]

    plans = get_plans_by_name(new_plan)

    await state.update_data(new_plan=new_plan)
    await state.set_state(ChangeTariffState.choosing_period)

    plan_emoji = {"Start": "🟢", "Plus": "🔵", "Pro": "🟣"}

    await message.answer(
        f"💳 Новый тариф:\n\n"
        f"Было:\n{plan_emoji.get(current_plan, '')} {current_plan}\n\n"
        f"Стало:\n{plan_emoji.get(new_plan, '')} {new_plan}\n\n"
        f"Выберите срок:",
        reply_markup=period_keyboard(plans)
    )


@router.message(ChangeTariffState.choosing_period, F.text.contains("месяц"))
async def change_tariff_period_chosen(message: Message, state: FSMContext):
    data = await state.get_data()
    new_plan = data.get("new_plan")

    parts = message.text.split(" — ")
    if len(parts) != 2:
        await message.answer("❌ Некорректный выбор. Попробуйте снова.")
        return

    period, price = parts[0], parts[1]

    create_order(
        telegram_id=message.from_user.id,
        plan=new_plan,
        period=period,
        amount=price,
    )

    await state.clear()

    await message.answer(
        get_order_screen_text(
            plan=new_plan,
            period=period,
            amount=price,
            status="pending",
        ),
        reply_markup=payment_pay_keyboard(),
    )
    await message.answer(
        "Доступные действия 👇",
        reply_markup=payment_keyboard(),
    )


# ======================
# УСТРОЙСТВА
# ======================

@router.message(F.text == "⚙️ Устройства")
async def devices(message: Message):
    profile = get_profile(message.from_user.id)

    if not profile or not profile[3]:
        await message.answer(
            "⚙️ Устройства\n\n"
            "❌ У вас нет активной подписки.\n\n"
            "Для подключения устройств необходимо оформить подписку.",
            reply_markup=profile_keyboard()
        )
        return

    plan = profile[3]
    devices_used = profile[9] or 0

    max_devices = {"Start": 2, "Plus": 5, "Pro": 10}
    limit = max_devices.get(plan, 0)

    await message.answer(
        f"⚙️ Устройства\n\n"
        f"Ваши устройства:\n\n"
        f"Использовано:\n"
        f"{devices_used} / {limit} устройств\n\n"
        f"Вы можете подключать VPN на нескольких устройствах одновременно "
        f"в рамках вашего тарифа.",
        reply_markup=devices_keyboard()
    )


@router.message(F.text == "⬅️ К выбору платформы")
async def back_to_guide(message: Message):
    await message.answer(
        GUIDE_TEXT,
        reply_markup=guide_keyboard()
    )



# ======================
# ОПЛАТА (Platega-ready stubs)
# ======================

@router.callback_query(F.data == "payment:pay")
async def pay_button(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        payment_pay_stub_text(),
        reply_markup=payment_keyboard(),
    )


@router.message(F.text == "🔄 Проверить оплату")
async def check_payment_button(message: Message):
    await message.answer(
        payment_check_stub_text(),
        reply_markup=payment_keyboard(),
    )


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