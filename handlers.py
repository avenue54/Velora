import random
from aiogram import Router, F
from datetime import datetime, timezone, timedelta
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.context import FSMContext

from keyboards import (
    main_menu_reply_keyboard,
    main_menu_news_keyboard,
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
    referral_keyboard,
    platform_ios_keyboard,
    platform_android_keyboard,
    platform_windows_keyboard,
    platform_macos_keyboard,
    get_config_keyboard,
    guide_support_keyboard,
    payment_keyboard,
    payment_pay_keyboard,
    documents_keyboard,
    document_link_keyboard,
)
from texts import (
    WELCOME_TEXT,
    TRIAL_TEXT,
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
    MAIN_MENU_TEXTS,
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
    GUIDE_SUPPORT_TEXT,
    DOCUMENTS_MENU_TEXT,
    PRIVACY_POLICY_TEXT,
    USER_AGREEMENT_TEXT,
    PRICES_PUBLIC_TEXT,
    SUPPORT_CONTACTS_TEXT,
    PRIVACY_POLICY_URL,
    USER_AGREEMENT_URL,
)
from database import (
    add_user,
    get_user,
    get_plans,
    get_plans_by_name,
    get_plan_by_period,
    create_subscription,
    get_user_subscription,
    get_profile,
    get_referral_code,
    get_user_by_referral_code,
    set_referred_by,
    count_referrals,
    get_promo,
    is_promo_valid,
    apply_promo_use,
    count_device_slots,
    list_device_slots,
    add_device_slot,
    remove_device_slot,
    get_device_limit,
    get_referral_reward_by_payment,
    extend_active_subscription_days,
    grant_trial_subscription,
    is_user_subscription_active,
    expire_outdated_subscriptions,
    get_user_subscription_end_date,
    has_trial_been_granted,
)
from states import SubscriptionState, RenewalState, ChangeTariffState, DeviceState, PromoUserState
from services import (
    subscription_status_text,
    create_order,
    get_order_screen_text,
    start_platega_payment,
    check_platega_payment,
)
from platega import PlategaError
from database import get_last_payment
from api import create_vpn_subscription, VeloraAPIError
from config import CHANNEL_USERNAME, CHANNEL_LINK


def _fmt_end_msk(end_date: str) -> str:
    """end_date from DB (UTC naive) → display in Moscow time."""
    if not end_date:
        return ""
    try:
        end = datetime.strptime(str(end_date)[:19], "%Y-%m-%d %H:%M:%S")
        end = end.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=3)))
        return end.strftime("%d.%m.%y в %H:%M МСК")
    except Exception:
        return str(end_date)[:16]


router = Router()


# ======================
# ПРОВЕРКА ПОДПИСКИ НА КАНАЛ
# ======================

async def is_user_subscribed(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        }
    except Exception:
        return False



async def _send_trial_if_needed(
    message: Message,
    telegram_id: int | None = None,
    *,
    bot=None,
) -> None:
    """Пробная Start на 3 дня — только после подписки на канал, один раз."""
    tg_id = telegram_id or message.from_user.id
    check_bot = bot or message.bot
    # Обязательная проверка канала перед выдачей trial
    if not await is_user_subscribed(check_bot, tg_id):
        return
    ok, info = grant_trial_subscription(tg_id, days=3)
    if not ok:
        return
    from keyboards import get_config_keyboard
    await message.answer(
        TRIAL_TEXT + chr(10) + chr(10) + f"📅 До: <b>{info}</b>",
        reply_markup=get_config_keyboard(),
    )

# ======================
# START
# ======================

@router.message(CommandStart())
async def start(message: Message):
    expire_outdated_subscriptions()
    referred_by = None
    if message.text and " " in message.text:
        payload = message.text.split(maxsplit=1)[1].strip().upper()
        ref = get_user_by_referral_code(payload)
        if ref:
            referred_by = ref[0]

    add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        referred_by=None,
    )
    if referred_by and set_referred_by(message.from_user.id, referred_by):
        try:
            await message.bot.send_message(
                referred_by,
                f"🎉 По вашей ссылке зарегистрировался "
                f"{message.from_user.first_name or 'новый пользователь'}!",
            )
        except Exception:
            pass

    # Проверка подписки на канал
    if not await is_user_subscribed(message.bot, message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Я подписался — проверить", callback_data="check_sub")],
        ])
        await message.answer(
            "👋 Добро пожаловать в <b>VELORA</b>!\n\n"
            "Для доступа к боту нужно подписаться на наш канал новостей:\n"
            f"{CHANNEL_LINK}\n\n"
            "После подписки нажмите кнопку ниже.",
            reply_markup=kb
        )
        return

    # Уже подписан на канал → приветствие, затем пробник
    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu_reply_keyboard()
    )
    await _send_trial_if_needed(message, telegram_id=message.from_user.id, bot=message.bot)


@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery):
    subscribed = await is_user_subscribed(callback.bot, callback.from_user.id)

    if subscribed:
        try:
            await callback.message.delete()
        except Exception:
            pass

        # Сначала приветствие, пробник — только после подтверждённой подписки на канал
        await callback.message.answer(
            WELCOME_TEXT,
            reply_markup=main_menu_reply_keyboard()
        )
        await _send_trial_if_needed(
            callback.message,
            telegram_id=callback.from_user.id,
            bot=callback.bot,
        )
        await callback.answer("✅ Подписка подтверждена!")
    else:
        await callback.answer(
            "❌ Вы ещё не подписались на канал.\nПодпишитесь и нажмите кнопку снова.",
            show_alert=True
        )


# ======================
# ГЛАВНОЕ МЕНЮ
# ======================

@router.message(F.text == "🚀 Подключиться")
async def connect(message: Message):
    expire_outdated_subscriptions()
    has_active = is_user_subscription_active(message.from_user.id)
    if has_active:
        await _issue_config_with_device(message)
        return
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
    expire_outdated_subscriptions()
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
        days = (end - datetime.utcnow()).days
        if days < 0:
            days = 0
        expiry_str = _fmt_end_msk(end_date)

    active_now = is_user_subscription_active(message.from_user.id)
    if not plan or not active_now:
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

    expiry_line = f"\nИстекает {expiry_str}" if expiry_str else ""

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


async def _issue_config_with_device(message: Message) -> None:
    """Подключение: +1 слот устройства → выдача ссылки."""
    expire_outdated_subscriptions()
    profile = get_profile(message.from_user.id)
    has_active = is_user_subscription_active(message.from_user.id)
    nl = chr(10)

    if not has_active:
        await message.answer(
            GET_CONFIG_TEXT,
            reply_markup=get_config_keyboard(),
        )
        return

    plan = profile[3] or ""
    period = profile[4] or ""
    limit = get_device_limit(plan)
    used = len(list_device_slots(message.from_user.id))

    if used >= limit:
        await message.answer(
            f"❌ Лимит устройств тарифа <b>{plan}</b>: <b>{limit}</b>." + nl + nl
            + "Освободите слот: Аккаунт → ⚙️ Устройства → удалить." + nl
            + "Или смените тариф на больший.",
            reply_markup=get_config_keyboard(),
        )
        return

    slot_n = used + 1
    label = f"Устройство {slot_n}"
    ok, err = add_device_slot(message.from_user.id, label, limit)
    if not ok:
        await message.answer(f"❌ {err}", reply_markup=get_config_keyboard())
        return

    try:
        end_date = get_user_subscription_end_date(message.from_user.id)
        data = await create_vpn_subscription(
            telegram_id=message.from_user.id,
            plan=plan,
            period=period,
            end_date=end_date,
        )
        url = data["url"]
        await message.answer(
            "✅ <b>Подключение</b>" + nl + nl
            + f"📱 Слот: <b>{label}</b> ({slot_n}/{limit})" + nl + nl
            + "📥 Ссылка на конфиг:" + nl
            + f"<code>{url}</code>" + nl + nl
            + "Импорт в Hiddify / v2rayNG / Streisand." + nl
            + "Не пересылайте ссылку третьим лицам.",
            reply_markup=get_config_keyboard(),
        )
    except VeloraAPIError as e:
        slots = list_device_slots(message.from_user.id)
        if slots:
            remove_device_slot(slots[-1][0], message.from_user.id)
        print(f"get_config API error: {e} {getattr(e, 'body', None)}")
        await message.answer(
            "⚠️ Не удалось получить конфиг. Слот не занят." + nl
            + "Попробуйте ещё раз или напишите в поддержку.",
            reply_markup=get_config_keyboard(),
        )
    except Exception as e:
        slots = list_device_slots(message.from_user.id)
        if slots:
            remove_device_slot(slots[-1][0], message.from_user.id)
        print(f"get_config fail: {e}")
        await message.answer(
            "⚠️ Ошибка при выдаче конфигурации. Попробуйте позже.",
            reply_markup=get_config_keyboard(),
        )


@router.message(F.text == "📥 Получить конфигурацию")
async def get_config(message: Message):
    await _issue_config_with_device(message)


@router.message(F.text == "🔌 Подключить устройство")
async def connect_device_btn(message: Message):
    await _issue_config_with_device(message)


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
# ДОКУМЕНТЫ
# ======================

@router.message(F.text == "📄 Документы")
async def documents_menu(message: Message):
    await message.answer(
        DOCUMENTS_MENU_TEXT,
        reply_markup=documents_keyboard(),
    )


@router.message(F.text == "🔒 Политика конфиденциальности")
async def privacy_policy(message: Message):
    await message.answer(
        PRIVACY_POLICY_TEXT,
        reply_markup=document_link_keyboard(
            PRIVACY_POLICY_URL,
            "🔒 Открыть политику",
        ),
    )
    await message.answer(
        "Выберите документ:",
        reply_markup=documents_keyboard(),
    )


@router.message(F.text == "📜 Пользовательское соглашение")
async def user_agreement(message: Message):
    await message.answer(
        USER_AGREEMENT_TEXT,
        reply_markup=document_link_keyboard(
            USER_AGREEMENT_URL,
            "📜 Открыть соглашение",
        ),
    )
    await message.answer(
        "Выберите документ:",
        reply_markup=documents_keyboard(),
    )


@router.message(F.text == "💰 Цены и тарифы")
async def prices_public(message: Message):
    await message.answer(
        PRICES_PUBLIC_TEXT,
        reply_markup=documents_keyboard(),
    )


@router.message(F.text == "💬 Контакты поддержки")
async def support_contacts(message: Message):
    await message.answer(
        SUPPORT_CONTACTS_TEXT,
        reply_markup=documents_keyboard(),
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
async def start_tariff(message: Message, state: FSMContext):
    await state.update_data(plan="Start")
    await state.set_state(SubscriptionState.choosing_period)
    plans = get_plans_by_name("Start")
    await message.answer(
        START_TEXT,
        reply_markup=period_keyboard(plans)
    )


@router.message(F.text == "🔵 Plus ⭐")
async def plus_tariff(message: Message, state: FSMContext):
    await state.update_data(plan="Plus")
    await state.set_state(SubscriptionState.choosing_period)
    plans = get_plans_by_name("Plus")
    await message.answer(
        PLUS_TEXT,
        reply_markup=period_keyboard(plans)
    )


@router.message(F.text == "🟣 Pro")
async def pro_tariff(message: Message, state: FSMContext):
    await state.update_data(plan="Pro")
    await state.set_state(SubscriptionState.choosing_period)
    plans = get_plans_by_name("Pro")
    await message.answer(
        PRO_TEXT,
        reply_markup=period_keyboard(plans)
    )


# ======================
# ПОКУПКА
# ======================

@router.message(SubscriptionState.choosing_period, F.text.contains("месяц"))
async def buy_tariff(message: Message, state: FSMContext):
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
    expire_outdated_subscriptions()
    profile = get_profile(message.from_user.id)

    if not profile or not profile[3] or not is_user_subscription_active(message.from_user.id):
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
# УСТРОЙСТВА
# ======================
# УСТРОЙСТВА (слоты по тарифу)
# ======================

def _devices_text(telegram_id: int) -> tuple[str, bool]:
    """Текст экрана устройств. Returns (text, has_active_sub)."""
    expire_outdated_subscriptions()
    profile = get_profile(telegram_id)
    if not profile or not profile[3] or not is_user_subscription_active(telegram_id):
        nl = chr(10)
        return (
            "⚙️ <b>Устройства</b>" + nl + nl
            + "❌ Нет активной подписки." + nl
            + "Оформите тариф, чтобы добавлять устройства.",
            False,
        )
    plan = profile[3]
    limit = get_device_limit(plan)
    slots = list_device_slots(telegram_id)
    used = len(slots)
    nl = chr(10)
    parts = [
        "⚙️ <b>Устройства</b>",
        f"Тариф: <b>{plan}</b>",
        f"Слотов: <b>{used} / {limit}</b>",
        "",
    ]
    if slots:
        parts.append("Список:")
        for sid, label, created in slots:
            created_short = (created or "")[:16]
            parts.append(f"• {label}  <i>#{sid}</i>  <code>{created_short}</code>")
    else:
        parts.append("Пока пусто. «Подключиться» / «Получить конфигурацию» займёт слот и выдаст ссылку.")
    parts += [
        "",
        "Учёт устройств по тарифу. Один конфиг можно поставить "
        "на несколько устройств в пределах лимита.",
    ]
    return nl.join(parts), True


@router.message(F.text == "⚙️ Устройства")
async def devices(message: Message):
    text, has_sub = _devices_text(message.from_user.id)
    if not has_sub:
        await message.answer(text, reply_markup=profile_keyboard())
        return
    await message.answer(text, reply_markup=devices_keyboard())


@router.message(F.text == "➕ Добавить устройство")
async def device_add(message: Message, state: FSMContext):
    await state.clear()
    await _issue_config_with_device(message)



@router.message(DeviceState.waiting_label, F.text == "/cancel")
async def device_add_cancel(message: Message, state: FSMContext):
    await state.clear()
    text, _ = _devices_text(message.from_user.id)
    await message.answer("Отменено." + chr(10) + chr(10) + text, reply_markup=devices_keyboard())


@router.message(DeviceState.waiting_label)
async def device_label_save(message: Message, state: FSMContext):
    profile = get_profile(message.from_user.id)
    if not profile or not profile[3]:
        await state.clear()
        return
    plan = profile[3]
    limit = get_device_limit(plan)
    label = (message.text or "Устройство").strip()[:40]
    if not label:
        await message.answer("Название не может быть пустым.")
        return
    ok, err = add_device_slot(message.from_user.id, label, limit)
    await state.clear()
    if not ok:
        await message.answer(f"❌ {err}", reply_markup=devices_keyboard())
        return
    text, _ = _devices_text(message.from_user.id)
    await message.answer(
        f"✅ Добавлено: <b>{label}</b>" + chr(10) + chr(10) + text,
        reply_markup=devices_keyboard(),
    )


@router.message(F.text == "🗑 Освободить слот")
async def device_del_hint(message: Message):
    slots = list_device_slots(message.from_user.id)
    if not slots:
        await message.answer("Нечего удалять.", reply_markup=devices_keyboard())
        return
    rows = [
        [InlineKeyboardButton(text=f"🗑 {label}", callback_data=f"devdel:{sid}")]
        for sid, label, _ in slots
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="devdel:cancel")])
    await message.answer(
        "Какой слот освободить?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data == "devdel:cancel")
async def device_del_cancel(callback: CallbackQuery):
    await callback.answer()
    text, _ = _devices_text(callback.from_user.id)
    try:
        await callback.message.edit_text(text)
    except Exception:
        await callback.message.answer(text, reply_markup=devices_keyboard())


@router.callback_query(F.data.startswith("devdel:"))
async def device_del_cb(callback: CallbackQuery):
    if callback.data == "devdel:cancel":
        return
    sid = int(callback.data.split(":")[1])
    if remove_device_slot(sid, callback.from_user.id):
        await callback.answer("Удалено")
        text, _ = _devices_text(callback.from_user.id)
        body = "✅ Удалено" + chr(10) + chr(10) + text
        try:
            await callback.message.edit_text(body)
        except Exception:
            await callback.message.answer(body, reply_markup=devices_keyboard())
    else:
        await callback.answer("Не найдено", show_alert=True)


@router.message(F.text == "🎁 Рефералка / промо")
async def referral_menu(message: Message):
    code = get_referral_code(message.from_user.id)
    n = count_referrals(message.from_user.id)
    bot_info = await message.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={code}"
    nl = chr(10)
    msg = (
        "🎁 <b>Реферальная программа</b>" + nl + nl
        + f"Ваш код: <code>{code}</code>" + nl
        + "Ссылка:" + nl + f"<code>{link}</code>" + nl + nl
        + f"Приглашено: <b>{n}</b>" + nl + nl
        + "Когда друг <b>оплатит</b> подписку — вам начислят "
        + "<b>+3 дня</b> к вашей подписке." + nl + nl
        + "Промокоды — кнопкой ниже."
    )
    await message.answer(msg, reply_markup=referral_keyboard())


@router.message(F.text == "🎟 Ввести промокод")
async def promo_user_start(message: Message, state: FSMContext):
    await state.set_state(PromoUserState.waiting_code)
    await message.answer("Введите промокод:")


@router.message(PromoUserState.waiting_code)
async def promo_user_apply(message: Message, state: FSMContext):
    code = (message.text or "").strip().upper()
    promo = get_promo(code)
    await state.clear()
    ok, err = is_promo_valid(promo)
    if not ok:
        await message.answer(f"❌ {err}")
        return
    bonus_days = int(promo[3] or 0)
    if not apply_promo_use(promo[0], message.from_user.id):
        await message.answer("❌ Вы уже использовали этот промокод.")
        return

    ok, info = extend_active_subscription_days(message.from_user.id, bonus_days)
    nl = chr(10)

    # синхрон срока на API (Happ /sub)
    if ok and info and info != "stored_bonus":
        try:
            profile = get_profile(message.from_user.id)
            plan = (profile[3] if profile else None) or "Start"
            period = (profile[4] if profile else None) or ""
            await create_vpn_subscription(
                telegram_id=message.from_user.id,
                plan=plan,
                period=period,
                end_date=info,
            )
        except Exception as e:
            print(f"promo API sync fail: {e}")

    if ok and info != "stored_bonus":
        end_show = _fmt_end_msk(info) if info else info
        await message.answer(
            f"✅ Промокод <code>{promo[1]}</code> применён!" + nl + nl
            + f"Вам начислено <b>+{bonus_days} дн.</b> к подписке." + nl
            + f"Новая дата окончания: <b>{end_show}</b>"
        )
    elif ok:
        await message.answer(
            f"✅ Промокод <code>{promo[1]}</code> принят!" + nl + nl
            + f"Вам начислено <b>+{bonus_days} дн.</b>." + nl
            + "Активной подписки нет — дни добавятся при активации."
        )
    else:
        await message.answer(
            "✅ Промокод учтён, но не удалось продлить подписку. "
            "Напишите в поддержку."
        )

@router.callback_query(F.data == "payment:pay")
async def pay_button(callback: CallbackQuery):
    await callback.answer()
    tg_id = callback.from_user.id
    payment = get_last_payment(tg_id)
    if not payment:
        await callback.message.answer(
            "❌ Заказ не найден. Выберите тариф заново.",
            reply_markup=payment_keyboard(),
        )
        return

    payment_id = payment[0]
    plan = payment[2]
    period = payment[3]
    amount = payment[4]
    status = payment[5]

    if status == "paid":
        await callback.message.answer(
            "✅ Этот заказ уже оплачен.\n"
            "Конфиг: «📥 Получить конфигурацию».",
            reply_markup=payment_keyboard(),
        )
        return

    try:
        result = await start_platega_payment(
            telegram_id=tg_id,
            payment_id=payment_id,
            plan=plan,
            period=period,
            amount_str=amount,
        )
        redirect = result["redirect"]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Перейти к оплате", url=redirect)],
            [InlineKeyboardButton(text="🔄 Я оплатил — проверить", callback_data="payment:check")],
        ])
        await callback.message.answer(
            f"💳 <b>Оплата VELORA</b>\n\n"
            f"Тариф: <b>{plan}</b>\n"
            f"Срок: <b>{period}</b>\n"
            f"Сумма: <b>{amount}</b>\n\n"
            "Нажмите кнопку ниже, оплатите, затем «Я оплатил — проверить».\n"
            "После оплаты конфиг придёт автоматически.",
            reply_markup=kb,
        )
    except PlategaError as e:
        print(f"Platega pay error: {e} body={getattr(e, 'body', None)}")
        await callback.message.answer(
            "⚠️ Не удалось создать ссылку на оплату.\n"
            "Попробуйте позже или напишите в поддержку.",
            reply_markup=payment_keyboard(),
        )
    except Exception as e:
        print(f"pay_button fail: {e}")
        await callback.message.answer(
            "⚠️ Ошибка при создании оплаты. Попробуйте позже.",
            reply_markup=payment_keyboard(),
        )


@router.callback_query(F.data == "payment:check")
async def payment_check_callback(callback: CallbackQuery):
    await callback.answer()
    result = await check_platega_payment(callback.from_user.id)
    if result.get("status") == "paid":
        try:
            from database import get_last_payment
            pay = get_last_payment(callback.from_user.id)
            if pay:
                rew = get_referral_reward_by_payment(pay[0])
                if rew:
                    await callback.bot.send_message(
                        rew[0],
                        "🎁 <b>Реферальный бонус!</b>\n\n"
                        "Ваш друг оплатил подписку. Вам <b>+3 дня</b>.",
                    )
        except Exception as e:
            print("referral notify", e)
    await callback.message.answer(
        result["message"],
        reply_markup=payment_keyboard(),
    )


@router.message(F.text == "🔄 Проверить оплату")
async def check_payment_button(message: Message):
    result = await check_platega_payment(message.from_user.id)
    await message.answer(
        result["message"],
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
async def main_menu(message: Message, state: FSMContext):
    await state.clear()
    expire_outdated_subscriptions()
    text = "🌐 VELORA\n\nБезопасное соединение активно.\n\nВыберите раздел 👇"
    text = (
        text
        + chr(10)
        + chr(10)
        + f'<a href="{CHANNEL_LINK}">📰 VELORA News</a>'
    )
    await message.answer(
        text,
        reply_markup=main_menu_reply_keyboard(),
    )
    
@router.message(F.photo)
async def get_photo_id(message: Message):
    file_id = message.photo[-1].file_id
    await message.answer(f"file_id:\n<code>{file_id}</code>")