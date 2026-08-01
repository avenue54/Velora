"""
Бизнес-логика заказов и оплаты.

Сейчас Platega API не подключён.
После появления ключей достаточно дописать вызовы API
внутри этих функций — handlers менять не нужно.
"""

from database import (
    create_payment,
    get_payment,
    get_last_payment,
    update_payment_status,
    create_subscription,
    activate_subscription as db_activate_subscription,
)


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
    Создать заказ (платёж pending).
    Подписка здесь НЕ создаётся.
    Возвращает payment_id или None.
    """
    return create_payment(
        telegram_id=telegram_id,
        plan=plan,
        period=period,
        amount=amount,
        provider="platega",
    )


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


def payment_pay_stub_text() -> str:
    """Ответ на кнопку «Оплатить», пока API нет."""
    return (
        "💳 Оплата через Platega будет подключена позже.\n\n"
        "Здесь появится ссылка на оплату."
    )


def payment_check_stub_text() -> str:
    """Ответ на кнопку «Проверить оплату», пока API нет."""
    return (
        "🔄 Оплата пока не подтверждена.\n\n"
        "После подключения Platega здесь будет выполняться "
        "автоматическая проверка."
    )


def payment_success(payment_id: int, provider_payment_id=None) -> bool:
    """
    Успешная оплата (вызывать из webhook / проверки Platega).

    Цепочка:
    update_payment_status(paid)
    → create_subscription
    → activate_subscription
    """
    payment = get_payment(payment_id)
    if not payment:
        return False

    # payments: id, telegram_id, plan, period, amount, status, provider, provider_payment_id, created_at, paid_at
    telegram_id = payment[1]
    plan = payment[2]
    period = payment[3]
    amount = payment[4]
    status = payment[5]

    if status == "paid":
        return True  # уже обработан

    update_payment_status(
        payment_id,
        "paid",
        provider_payment_id=provider_payment_id,
    )

    # Создаём и сразу активируем подписку
    create_subscription(
        telegram_id=telegram_id,
        plan=plan,
        period=period,
        price=amount,
    )

    # Активируем последнюю pending-подписку пользователя через get_last...
    # create_subscription создаёт pending — нужно активировать по id.
    # Для этого найдём последнюю подписку пользователя.
    from database import get_connection

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

    return True


def payment_failed(payment_id: int) -> bool:
    """Отметить платёж как failed."""
    payment = get_payment(payment_id)
    if not payment:
        return False
    update_payment_status(payment_id, "failed")
    return True


def cancel_payment(payment_id: int) -> bool:
    """Отменить платёж."""
    payment = get_payment(payment_id)
    if not payment:
        return False
    if payment[5] == "paid":
        return False
    update_payment_status(payment_id, "cancelled")
    return True


def activate_subscription_from_payment(payment_id: int) -> bool:
    """Алиас для явной активации после оплаты (на будущее)."""
    return payment_success(payment_id)
