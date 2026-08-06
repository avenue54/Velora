"""
services.py —
Бизнес-логика заказов и оплаты (Platega).
"""

from __future__ import annotations

import logging
from typing import Optional

from database import (
    create_payment,
    get_payment,
    get_last_payment,
    update_payment_status,
    create_subscription,
    activate_subscription as db_activate_subscription,
    get_connection,
    grant_referral_bonus_for_payment,  
)


from platega import (
    PlategaError,
    parse_amount_rub,
    create_payment_link,
    get_transaction_status,
    normalize_webhook_status,
)

logger = logging.getLogger(__name__)


def subscription_status_text(status: str) -> str:
    if status == "active":
        return "🟢 Активна"
    if status == "pending":
        return "🟡 Ожидает подтверждения"
    if status == "rejected":
        return "🔴 Не оплачена"
    return "⚪ Неизвестно"


def create_order(telegram_id: int, plan: str, period: str, amount: str):
    """
    Создать заказ: платёж (pending) + заявку на подписку (pending).
    Возвращает payment_id.
    """
    payment_id = create_payment(
        telegram_id=telegram_id,
        plan=plan,
        period=period,
        amount=amount,
        provider="platega",
    )

    create_subscription(
        telegram_id=telegram_id,
        plan=plan,
        period=period,
        price=amount,
    )

    return payment_id


def get_order_screen_text(plan: str, period: str, amount: str, status: str = "pending") -> str:
    status_line = {
        "pending": "⏳ Ожидает оплаты",
        "paid": "✅ Оплачен",
        "failed": "❌ Ошибка оплаты",
        "cancelled": "🚫 Отменён",
    }.get(status, status)

    return (
        "💳 Ваш заказ\n\n"
        f"Тариф:\n{plan}\n\n"
        f"Срок:\n{period}\n\n"
        f"Стоимость:\n{amount}\n\n"
        f"Статус:\n{status_line}\n\n"
        "После успешной оплаты подписка активируется автоматически."
    )


async def start_platega_payment(
    telegram_id: int,
    payment_id: int,
    plan: str,
    period: str,
    amount_str: str,
) -> dict:
    """
    Создаёт ссылку на оплату в Platega.
    Возвращает {"redirect": "...", "transaction_id": "..."}.
    """
    amount = parse_amount_rub(amount_str)
    payload = f"payment_id={payment_id};tg={telegram_id};plan={plan};period={period}"

    result = await create_payment_link(
        amount_rub=amount,
        description=f"VELORA {plan} ({period})",
        payload=payload,
        # payment_method=None → общая форма Platega (СБП / карта / крипта)
    )

    # Сохраняем transactionId от Platega
    update_payment_status(
        payment_id,
        "pending",
        provider_payment_id=result["transaction_id"],
    )
    return result


async def check_platega_payment(telegram_id: int) -> dict:
    """
    Проверка последнего платежа пользователя через API Platega.
    Возвращает {"status": "...", "message": "..."}.
    """
    payment = get_last_payment(telegram_id)
    if not payment:
        return {"status": "none", "message": "Заказов пока нет."}

    # payments: id, telegram_id, plan, period, amount, status, provider, provider_payment_id, ...
    payment_id = payment[0]
    plan = payment[2]
    period = payment[3]
    amount = payment[4]
    status = payment[5]
    provider_tx = payment[7] if len(payment) > 7 else None

    if status == "paid":
        return {
            "status": "paid",
            "message": (
                f"✅ Заказ уже оплачен.\n\n"
                f"Тариф: {plan}\nСрок: {period}\n"
                "Конфиг: «📥 Получить конфигурацию»."
            ),
        }

    if not provider_tx:
        return {
            "status": "pending",
            "message": (
                "⏳ Ссылка на оплату ещё не создавалась.\n"
                "Нажмите «💳 Оплатить»."
            ),
        }

    try:
        data = await get_transaction_status(provider_tx)
        raw = data.get("status") or data.get("Status")
        norm = normalize_webhook_status(raw)

        if norm == "confirmed":
            payment_success(payment_id, provider_payment_id=provider_tx)
            return {
                "status": "paid",
                "message": (
                    f"✅ Оплата подтверждена!\n\n"
                    f"Тариф: {plan}\nСрок: {period}\n\n"
                    "Подписка активирована. "
                    "Получите конфиг: «📥 Получить конфигурацию»."
                ),
            }
        if norm == "canceled":
            payment_failed(payment_id)
            return {
                "status": "failed",
                "message": "❌ Оплата отменена или не прошла. Оформите тариф заново.",
            }
        return {
            "status": "pending",
            "message": (
                f"⏳ Оплата ещё не поступила (статус: {raw}).\n\n"
                f"Сумма: {amount}\n"
                "Если уже оплатили — подождите 1–2 минуты и нажмите снова."
            ),
        }
    except PlategaError as e:
        logger.error("check_platega_payment: %s", e)
        return {
            "status": "error",
            "message": "⚠️ Не удалось проверить оплату. Попробуйте позже.",
        }


def payment_pay_stub_text() -> str:
    return (
        "💳 Оплата через Platega будет подключена позже.\n\n"
        "Здесь появится ссылка на оплату."
    )


def payment_check_stub_text() -> str:
    return (
        "🔄 Оплата пока не подтверждена.\n\n"
        "После подключения Platega здесь будет выполняться "
        "автоматическая проверка."
    )


def payment_success(payment_id: int, provider_payment_id=None) -> bool:
    """
    Успешная оплата (webhook / проверка статуса).
    """
    payment = get_payment(payment_id)
    if not payment:
        return False

    telegram_id = payment[1]
    plan = payment[2]
    period = payment[3]
    amount = payment[4]
    status = payment[5]

    if status == "paid":
        return True

    update_payment_status(
        payment_id,
        "paid",
        provider_payment_id=provider_payment_id,
    )

    # Активируем последнюю pending-подписку
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT subscriptions.id
        FROM subscriptions
        JOIN users ON subscriptions.user_id = users.id
        WHERE users.telegram_id = ?
          AND subscriptions.status = 'pending'
        ORDER BY subscriptions.id DESC
        LIMIT 1
        """,
        (telegram_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        db_activate_subscription(row[0])
    else:
        # на всякий случай создаём и активируем
        create_subscription(
            telegram_id=telegram_id,
            plan=plan,
            period=period,
            price=amount,
        )
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT subscriptions.id
            FROM subscriptions
            JOIN users ON subscriptions.user_id = users.id
            WHERE users.telegram_id = ?
              AND subscriptions.status = 'pending'
            ORDER BY subscriptions.id DESC
            LIMIT 1
            """,
            (telegram_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            db_activate_subscription(row[0])

    # Реферальный бонус: +3 дня пригласившему
    try:
        bonus = grant_referral_bonus_for_payment(telegram_id, payment_id, days=3)
        if bonus.get("granted"):
            logger.info(
                "Referral +3d: buyer=%s referrer=%s end=%s",
                telegram_id,
                bonus.get("referrer"),
                bonus.get("new_end"),
            )
            # сохраним в «глобальный» атрибут для уведомления из handlers/webhook
            payment_success.last_referral_bonus = bonus  # type: ignore
        else:
            payment_success.last_referral_bonus = bonus  # type: ignore
    except Exception as e:
        logger.exception("Referral bonus error: %s", e)
        payment_success.last_referral_bonus = None  # type: ignore

    return True


def payment_failed(payment_id: int) -> bool:
    payment = get_payment(payment_id)
    if not payment:
        return False
    update_payment_status(payment_id, "failed")
    return True


def cancel_payment(payment_id: int) -> bool:
    payment = get_payment(payment_id)
    if not payment:
        return False
    if payment[5] == "paid":
        return False
    update_payment_status(payment_id, "cancelled")
    return True


def activate_subscription_from_payment(payment_id: int) -> bool:
    return payment_success(payment_id)
