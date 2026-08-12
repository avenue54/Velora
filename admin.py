# admin.py — панель с паролем и именем
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
    is_admin_password_set,
    check_admin_password,
    set_admin_password,
    get_admin_display_name,
    set_admin_display_name,
    create_promo_code,
    list_promo_codes,
    deactivate_promo,
    admin_get,
    get_promo_usage_stats,
    get_promo_users,
)
from keyboard_admin import (
    admin_main_keyboard,
    subscription_admin_keyboard,
    broadcast_cancel_keyboard,
)
from admin_texts import (
    ADMIN_PANEL_TEXT,
    STATISTICS_TEXT,
    admin_welcome,
)
from config import ADMIN_ID
from states import BroadcastState, AdminAuthState, PromoAdminState
from api import create_vpn_subscription, VeloraAPIError
from database import get_connection

router = Router()

# Сессии: telegram_id -> True после успешного ввода пароля (до рестарта бота)
_admin_sessions: set[int] = set()


def _is_owner(tg_id: int) -> bool:
    return tg_id == ADMIN_ID


def _is_authed(tg_id: int) -> bool:
    return _is_owner(tg_id) and tg_id in _admin_sessions


# ======================
# /admin → пароль → имя
# ======================

@router.message(Command("admin"))
async def admin_entry(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id):
        return

    await state.clear()

    # Первый запуск: задать пароль
    if not is_admin_password_set():
        await state.set_state(AdminAuthState.waiting_new_password)
        await message.answer(
            "🛠 <b>Настройка админ-панели</b>\n\n"
            "Пароль ещё не задан.\n"
            "Придумайте пароль (минимум 6 символов) и отправьте его сюда.\n\n"
            "⚠️ Сообщение с паролем лучше потом удалить из чата."
        )
        return

    # Уже в сессии
    if _is_authed(message.from_user.id):
        name = get_admin_display_name()
        await message.answer(
            admin_welcome(name),
            reply_markup=admin_main_keyboard(),
        )
        return

    await state.set_state(AdminAuthState.waiting_password)
    await message.answer(
        "🔐 <b>Вход в админ-панель</b>\n\n"
        "Введите пароль:"
    )


@router.message(AdminAuthState.waiting_new_password)
async def admin_set_password(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id):
        return
    pwd = (message.text or "").strip()
    if len(pwd) < 6:
        await message.answer("Пароль слишком короткий. Минимум 6 символов.")
        return
    set_admin_password(pwd)
    try:
        await message.delete()
    except Exception:
        pass
    await state.set_state(AdminAuthState.waiting_name)
    await message.answer(
        "✅ Пароль сохранён.\n\n"
        "Как к вам обращаться? Напишите имя (например: Даниил):"
    )


@router.message(AdminAuthState.waiting_password)
async def admin_check_password(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id):
        return
    pwd = (message.text or "").strip()
    try:
        await message.delete()
    except Exception:
        pass
    if not check_admin_password(pwd):
        await message.answer("❌ Неверный пароль. /admin — попробовать снова.")
        await state.clear()
        return

    _admin_sessions.add(message.from_user.id)
    name = get_admin_display_name()
    if not admin_get_name_set():
        await state.set_state(AdminAuthState.waiting_name)
        await message.answer("✅ Пароль верный.\n\nКак к вам обращаться? Напишите имя:")
        return

    await state.clear()
    await message.answer(
        admin_welcome(name),
        reply_markup=admin_main_keyboard(),
    )


def admin_get_name_set() -> bool:
    return bool(admin_get("display_name"))


@router.message(AdminAuthState.waiting_name)
async def admin_set_name(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id):
        return
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Имя слишком короткое. Попробуйте ещё раз:")
        return
    set_admin_display_name(name)
    _admin_sessions.add(message.from_user.id)
    await state.clear()
    await message.answer(
        admin_welcome(name),
        reply_markup=admin_main_keyboard(),
    )


def _require_admin(message: Message) -> bool:
    if not _is_owner(message.from_user.id):
        return False
    if not _is_authed(message.from_user.id):
        return False
    return True


# ======================
# ПУНКТЫ МЕНЮ
# ======================

@router.message(F.text == "👥 Пользователи")
async def users_list(message: Message):
    if not _require_admin(message):
        return

    users = get_all_users()
    if not users:
        await message.answer("Пользователей пока нет.")
        return

    text = "👥 <b>Пользователи</b> (последние 30):\n\n"
    for user in users[-30:]:
        text += (
            f"• ID {user[0]} | TG <code>{user[1]}</code>\n"
            f"  {user[3] or '—'} | @{user[2] or '—'} | {user[4]}\n"
        )
    await message.answer(text)


@router.message(F.text == "💳 Подписки")
async def subscriptions_list(message: Message):
    if not _require_admin(message):
        return

    data = get_subscriptions()
    if not data:
        await message.answer("💳 Подписок пока нет")
        return

    for sub in data[:20]:
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
            f"👤 {name}\n"
            f"🆔 <code>{telegram_id}</code>\n"
            f"💳 {plan} · {period} · {price}\n"
            f"📊 {status}\n"
            f"🕒 {date}"
        )
        await message.answer(
            text,
            reply_markup=subscription_admin_keyboard(sub_id),
        )


@router.message(F.text == "📊 Статистика")
async def statistics(message: Message):
    if not _require_admin(message):
        return

    stats = get_statistics()
    if isinstance(stats, dict):
        text = STATISTICS_TEXT.format(
            users=stats.get("users", 0),
            subscriptions=stats.get("subscriptions", 0),
            active=stats.get("active", 0),
            pending=stats.get("pending", 0),
        )
    elif isinstance(stats, (tuple, list)) and len(stats) >= 4:
        text = STATISTICS_TEXT.format(
            users=stats[0],
            subscriptions=stats[1],
            active=stats[2],
            pending=stats[3],
        )
    else:
        text = f"📊 Статистика:\n{stats}"
    await message.answer(text)


@router.message(F.text == "🎁 Промокоды")
async def promo_menu(message: Message, state: FSMContext):
    if not _require_admin(message):
        return
    rows = list_promo_codes()
    text = "🎁 <b>Промокоды</b>\n\n"
    if not rows:
        text += "Пока нет промокодов.\n"
    else:
        for r in rows[:20]:
            # id, code, discount, bonus_days, max_uses, used, active, expires
            status = "🟢" if r[6] else "🔴"
            text += (
                f"{status} <code>{r[1]}</code> — +{r[3]} дн. "
                f"до {r[7] or '∞'} ({r[5]} исп.)\n"
            )
    text += (
        "\nСоздать: /new_promo\n"
        "Статистика: /promo_stats\n"
        "Кто использовал: /promo_stats КОД\n"
        "Отключить: /promo_off КОД"
    )
    await message.answer(text)


@router.message(Command("promo_stats"))
async def promo_stats(message: Message):
    if not _require_admin(message):
        return

    parts = (message.text or "").split(maxsplit=1)

    # /promo_stats  — сводка по всем
    if len(parts) == 1:
        rows = get_promo_usage_stats()
        if not rows:
            await message.answer("Пока нет промокодов.")
            return
        lines = ["📊 <b>Использование промокодов</b>\n"]
        for code, used, active in rows:
            mark = "🟢" if active else "🔴"
            lines.append(f"{mark} <code>{code}</code> — <b>{used}</b> чел.")
        lines.append("\nДетали по коду:\n<code>/promo_stats КОД</code>")
        await message.answer("\n".join(lines))
        return

    # /promo_stats CODE — кто использовал
    code = parts[1].strip().upper()
    users = get_promo_users(code)
    if not users:
        await message.answer(
            f"По коду <code>{code}</code> использований нет "
            f"(или такого промокода нет).",
        )
        return

    lines = [f"👥 <b>{code}</b> — {len(users)} чел.\n"]
    for tg_id, used_at in users[:50]:
        lines.append(f"• <code>{tg_id}</code> — {used_at}")
    if len(users) > 50:
        lines.append(f"\n…и ещё {len(users) - 50}")
    await message.answer("\n".join(lines))


@router.message(Command("new_promo"))
async def new_promo(message: Message, state: FSMContext):
    if not _require_admin(message):
        return
    await state.set_state(PromoAdminState.waiting_code)
    await message.answer(
        "🎁 <b>Новый промокод</b>\n\n"
        "1. Название (код, который вводят пользователи)\n\n"
        "Напишите название:"
    )


@router.message(Command("promo_new"))  # алиас
async def promo_new_alias(message: Message, state: FSMContext):
    await new_promo(message, state)


@router.message(PromoAdminState.waiting_code)
async def promo_code_entered(message: Message, state: FSMContext):
    if not _require_admin(message):
        return
    code = (message.text or "").strip().upper()
    if len(code) < 3:
        await message.answer("Слишком короткое название (мин. 3 символа).")
        return
    await state.update_data(code=code)
    await state.set_state(PromoAdminState.waiting_plan)
    await message.answer(
        "2. Какой тариф даёт промокод?\n\n"
        "• <code>Start</code>\n"
        "• <code>Plus</code>\n"
        "• <code>Pro</code>\n\n"
        "Напишите название тарифа:"
    )


@router.message(PromoAdminState.waiting_plan)
async def promo_plan_entered(message: Message, state: FSMContext):
    if not _require_admin(message):
        return
    plan = (message.text or "").strip().capitalize()
    if plan not in ("Start", "Plus", "Pro"):
        await message.answer("Неверный тариф. Напишите: Start, Plus или Pro")
        return
    await state.update_data(plan=plan)
    await state.set_state(PromoAdminState.waiting_bonus_days)
    await message.answer(
        f"3. Сколько <b>дней</b> тарифа <b>{plan}</b> даёт промокод?\n"
        "Напишите число (например 2):"
    )


@router.message(PromoAdminState.waiting_discount)
async def promo_discount_entered(message: Message, state: FSMContext):
    if not _require_admin(message):
        return
    await state.set_state(PromoAdminState.waiting_bonus_days)
    await message.answer("2. Сколько +дней? Напишите число:")


@router.message(PromoAdminState.waiting_bonus_days)
async def promo_bonus_entered(message: Message, state: FSMContext):
    if not _require_admin(message):
        return
    try:
        b = int((message.text or "0").strip())
    except ValueError:
        await message.answer("Нужно целое число дней.")
        return
    if b <= 0:
        await message.answer("Дни должны быть больше 0.")
        return
    await state.update_data(bonus_days=b)
    await state.set_state(PromoAdminState.waiting_expires)
    await message.answer(
        "4. Срок действия кода (в днях).\n"
        "• <b>0</b> — бессрочный\n"
        "• <b>30</b> — действует 30 дней\n\n"
        "Напишите число:"
    )


@router.message(PromoAdminState.waiting_max_uses)
async def promo_max_legacy(message: Message, state: FSMContext):
    """Старый шаг — перенаправляем на expires."""
    if not _require_admin(message):
        return
    await state.set_state(PromoAdminState.waiting_expires)
    await message.answer(
        "3. Окончание промо (дней, 0 = бессрочно):"
    )


@router.message(PromoAdminState.waiting_expires)
async def promo_expires_entered(message: Message, state: FSMContext):
    if not _require_admin(message):
        return
    try:
        exp_days = int((message.text or "0").strip())
    except ValueError:
        await message.answer("Нужно число (0 = бессрочно).")
        return
    if exp_days < 0:
        await message.answer("Не может быть отрицательным.")
        return
    data = await state.get_data()
    code = data["code"]
    days = int(data.get("bonus_days", 0))
    plan = data.get("plan", "Plus")
    ok = create_promo_code(
        code=code,
        bonus_days=days,
        expires_in_days=exp_days,
        discount_percent=0,
        max_uses=0,
        plan=plan,
    )
    await state.clear()
    if not ok:
        await message.answer("❌ Не удалось создать (возможно, такое название уже есть).")
        return
    exp_txt = "бессрочно" if exp_days == 0 else f"{exp_days} дн. с сегодня"
    nl = chr(10)
    await message.answer(
        f"✅ Промокод <code>{code}</code> создан" + nl + nl
        + f"• Тариф: {plan}" + nl
        + f"• +{days} дн. подписки" + nl
        + f"• Срок действия кода: {exp_txt}",
        reply_markup=admin_main_keyboard(),
    )


@router.message(Command("promo_off"))
async def promo_off(message: Message):
    if not _require_admin(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /promo_off КОД")
        return
    deactivate_promo(parts[1])
    await message.answer(f"🔴 Промокод <code>{parts[1].strip().upper()}</code> отключён.")


@router.message(F.text == "📢 Рассылка")
async def broadcast_start(message: Message, state: FSMContext):
    if not _require_admin(message):
        return
    await state.set_state(BroadcastState.waiting_message)
    await message.answer(
        "📢 Отправьте сообщение для рассылки (текст).\n"
        "Или нажмите «❌ Отмена рассылки».",
        reply_markup=broadcast_cancel_keyboard(),
    )


@router.message(F.text == "❌ Отмена рассылки")
async def broadcast_cancel(message: Message, state: FSMContext):
    if not _require_admin(message):
        return
    await state.clear()
    await message.answer("Рассылка отменена.", reply_markup=admin_main_keyboard())


@router.message(BroadcastState.waiting_message)
async def broadcast_send(message: Message, state: FSMContext):
    if not _require_admin(message):
        return
    text = message.text or message.caption or ""
    if not text:
        await message.answer("Нужен текст.")
        return
    ids = get_all_telegram_ids()
    ok = fail = 0
    for tg_id in ids:
        try:
            await message.bot.send_message(tg_id, text)
            ok += 1
        except Exception:
            fail += 1
    await state.clear()
    await message.answer(
        f"✅ Рассылка: отправлено {ok}, ошибок {fail}.",
        reply_markup=admin_main_keyboard(),
    )


@router.message(F.text == "🏠 Главное меню")
async def admin_to_main(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id):
        return
    await state.clear()
    from keyboards import main_keyboard
    await message.answer("Главное меню", reply_markup=main_keyboard())


@router.message(Command("admin_logout"))
async def admin_logout(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id):
        return
    _admin_sessions.discard(message.from_user.id)
    await state.clear()
    await message.answer("🔒 Вы вышли из админ-панели.")


@router.message(Command("admin_setpass"))
async def admin_change_pass(message: Message, state: FSMContext):
    if not _require_admin(message):
        return
    await state.set_state(AdminAuthState.waiting_new_password)
    await message.answer("Введите новый пароль (мин. 6 символов):")


# ======================
# Активация / отклонение
# ======================

@router.callback_query(F.data.startswith("activate:"))
async def activate_sub(callback: CallbackQuery):
    if not _is_authed(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    sub_id = int(callback.data.split(":")[1])
    activate_subscription(sub_id)
    tg_id = get_subscription_user_telegram_id(sub_id)
    try:
        if tg_id:
            await create_vpn_subscription(tg_id)
            await callback.bot.send_message(
                tg_id,
                f"✅ Подписка #{sub_id} активирована!\n"
                "Конфиг: «📥 Получить конфигурацию».",
            )
    except VeloraAPIError as e:
        await callback.message.answer(f"Подписка в БД ок, API: {e}")
    except Exception as e:
        await callback.message.answer(f"Уведомление: {e}")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Активировано")
    await callback.message.answer(f"✅ Подписка #{sub_id} активирована")


@router.callback_query(F.data.startswith("reject:"))
async def reject_sub(callback: CallbackQuery):
    if not _is_authed(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    sub_id = int(callback.data.split(":")[1])
    update_subscription_status(sub_id, "rejected")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Отклонено")
    await callback.message.answer(f"❌ Подписка #{sub_id} отклонена")