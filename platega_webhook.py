"""
Обработчик webhook Platega для FastAPI (getvelora.xyz).

Подключение в app.py:
    from platega_webhook import router as platega_router
    app.include_router(platega_router)

Callback URL в ЛК Platega:
    https://getvelora.xyz/platega/webhook

Обработка ошибок:
  - 401 — неверные X-MerchantId / X-Secret
  - 400 — битое тело / нет обязательных полей
  - 200 — всегда при успешной приёмке (даже если бизнес-логика
           уже обработала этот платёж ранее), чтобы Platega
           не делала повторные попытки
  - 500 — только при неожиданном падении (Platega повторит до 3 раз)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import aiohttp
from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger("platega.webhook")

try:
    from services import payment_success, payment_failed
except Exception:  # pragma: no cover
    payment_success = None  # type: ignore
    payment_failed = None  # type: ignore

try:
    from database import grant_referral_bonus_for_payment, get_referral_reward_by_payment
except Exception:
    grant_referral_bonus_for_payment = None  # type: ignore


router = APIRouter(prefix="/platega", tags=["platega"])

PLATEGA_MERCHANT_ID = os.getenv("PLATEGA_MERCHANT_ID", "")
PLATEGA_SECRET = os.getenv("PLATEGA_SECRET", "")
BOT_TOKEN = os.getenv("VELORA_BOT_TOKEN", "") or os.getenv("BOT_TOKEN", "")
VELORA_API_URL = os.getenv("VELORA_API_URL", "https://getvelora.xyz").rstrip("/")
VELORA_API_KEY = os.getenv("VELORA_API_KEY", "")


def _norm_status(raw: Any) -> str:
    if raw is None:
        return "unknown"
    s = str(raw).strip().upper()
    mapping = {
        "CONFIRMED": "confirmed",
        "PAID": "confirmed",
        "SUCCESS": "confirmed",
        "CANCELED": "canceled",
        "CANCELLED": "canceled",
        "FAILED": "canceled",
        "CHARGEBACK": "chargeback",
        "CHARGEBACKED": "chargeback",
        "PENDING": "pending",
        "7": "confirmed",
        "6": "canceled",
        "9": "chargeback",
        "1": "pending",
    }
    return mapping.get(s, "unknown")


def _verify_headers(merchant_id: Optional[str], secret: Optional[str]) -> bool:
    if not PLATEGA_MERCHANT_ID or not PLATEGA_SECRET:
        logger.error("PLATEGA_MERCHANT_ID/SECRET not configured on server")
        return False
    if not merchant_id or not secret:
        return False
    return (
        merchant_id.strip() == PLATEGA_MERCHANT_ID.strip()
        and secret.strip() == PLATEGA_SECRET.strip()
    )


async def _notify_user(telegram_id: int, text: str) -> bool:
    """Отправка сообщения пользователю через Bot API (без aiogram)."""
    if not BOT_TOKEN or not telegram_id:
        logger.warning("Cannot notify: no BOT_TOKEN or telegram_id")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=15) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("Telegram notify fail %s: %s", resp.status, body)
                    return False
                return True
    except Exception as e:
        logger.exception("Telegram notify error: %s", e)
        return False


async def _issue_vpn(telegram_id: int, plan: str = "Plus", period: str = "1 месяц") -> Optional[str]:
    """Вызов internal create-sub → URL конфига."""
    if not VELORA_API_KEY:
        logger.warning("VELORA_API_KEY missing, skip VPN issue")
        return None
    url = f"{VELORA_API_URL}/internal/create-sub"
    headers = {
        "X-API-Key": VELORA_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "telegram_id": int(telegram_id),
        "plan": plan or "Plus",
        "period": period or "1 месяц",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body, headers=headers, timeout=20) as resp:
                if resp.status != 200:
                    logger.error("create-sub %s: %s", resp.status, await resp.text())
                    return None
                data = await resp.json(content_type=None)
                return data.get("url")
    except Exception as e:
        logger.exception("create-sub error: %s", e)
        return None


@router.post("/webhook")
async def platega_webhook(
    request: Request,
    x_merchantid: Optional[str] = Header(default=None, alias="X-MerchantId"),
    x_secret: Optional[str] = Header(default=None, alias="X-Secret"),
    # Platega sometimes sends lowercase
    x_merchantid_lower: Optional[str] = Header(default=None, alias="x-merchantid"),
    x_secret_lower: Optional[str] = Header(default=None, alias="x-secret"),
):
    """
    Callback от Platega.

    Ожидаемое тело (примерно):
    {
      "Id": "<transactionId>",
      "amount": 129,
      "currency": "RUB",
      "status": "CONFIRMED",
      "payload": "payment_id=123;tg=8501117166;plan=Plus;period=1 месяц"
    }
    """
    merchant = x_merchantid or x_merchantid_lower
    secret = x_secret or x_secret_lower

    # --- 1. Auth ---
    if not _verify_headers(merchant, secret):
        logger.warning(
            "Webhook unauthorized: merchant=%r secret_set=%s",
            merchant,
            bool(secret),
        )
        return JSONResponse(
            status_code=401,
            content={"ok": False, "error": "unauthorized"},
        )

    # --- 2. Parse body ---
    try:
        raw_body = await request.body()
        if not raw_body:
            # Platega шлёт пустой POST при проверке Callback URL в ЛК
            logger.info("Webhook empty body (callback URL validation)")
            return JSONResponse(status_code=200, content={"ok": True, "message": "pong"})
        data = await request.json()
    except Exception as e:
        logger.error("Webhook bad JSON: %s", e)
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "invalid_json"},
        )

    if not isinstance(data, dict):
        logger.error("Webhook body is not object: %r", type(data))
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "body_must_be_object"},
        )

    transaction_id = (
        data.get("Id")
        or data.get("id")
        or data.get("transactionId")
        or data.get("transaction_id")
    )
    status_raw = data.get("status") or data.get("Status")
    payload = data.get("payload") or data.get("Payload") or ""
    amount = data.get("amount") or data.get("Amount")

    status = _norm_status(status_raw)

    logger.info(
        "Webhook received: tx=%s status=%s(%s) amount=%s payload=%r",
        transaction_id,
        status,
        status_raw,
        amount,
        payload,
    )

    # --- 3. Parse payload: payment_id=..;tg=..;plan=..;period=.. ---
    meta: dict[str, str] = {}
    if payload:
        for part in str(payload).split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                meta[k.strip()] = v.strip()

    payment_id = meta.get("payment_id")
    telegram_id_str = meta.get("tg") or meta.get("telegram_id")
    plan = meta.get("plan") or "Plus"
    period = meta.get("period") or "1 месяц"

    telegram_id: Optional[int] = None
    if telegram_id_str:
        try:
            telegram_id = int(telegram_id_str)
        except ValueError:
            logger.error("Bad telegram_id in payload: %r", telegram_id_str)

    # --- 4. Business logic (errors here → still 200, чтобы не было ретраев) ---
    try:
        if status == "confirmed":
            if not telegram_id:
                logger.error("CONFIRMED but no telegram_id in payload, tx=%s", transaction_id)
                # 200: Platega не должна ретраить — данные уже «приняты»
                return JSONResponse(
                    status_code=200,
                    content={"ok": True, "warning": "no_telegram_id"},
                )

            # Активация подписки в БД бота + реферальный бонус
            if payment_success and payment_id:
                try:
                    payment_success(int(payment_id), provider_payment_id=transaction_id)
                except Exception as e:
                    logger.exception("payment_success failed: %s", e)

            # Уведомление рефереру о +3 днях (начисление уже в payment_success)
            try:
                if payment_id:
                    reward = None
                    try:
                        from database import get_referral_reward_by_payment
                        reward = get_referral_reward_by_payment(int(payment_id))
                    except Exception:
                        reward = None
                    if reward:
                        referrer_tg = int(reward[0])
                        await _notify_user(
                            referrer_tg,
                            "🎁 <b>Реферальный бонус!</b>\n\n"
                            "Ваш друг оплатил подписку VELORA.\n"
                            "Вам начислено <b>+3 дня</b> к подписке.",
                        )
            except Exception as e:
                logger.exception("referral notify: %s", e)

            vpn_url = await _issue_vpn(telegram_id, plan=plan, period=period)

            if vpn_url:
                text = (
                    "✅ <b>Оплата прошла успешно!</b>\n\n"
                    f"Тариф: <b>{plan}</b>\n"
                    f"Срок: <b>{period}</b>\n\n"
                    "📥 Ваша конфигурация VELORA:\n"
                    f"<code>{vpn_url}</code>\n\n"
                    "Импортируйте ссылку в Hiddify / v2rayNG / Streisand.\n"
                    "Не пересылайте её третьим лицам."
                )
            else:
                text = (
                    "✅ <b>Оплата прошла успешно!</b>\n\n"
                    f"Тариф: <b>{plan}</b> ({period})\n\n"
                    "Подписка активируется. Если конфиг не пришёл — "
                    "нажмите «📥 Получить конфигурацию» в боте "
                    "или напишите в поддержку."
                )

            await _notify_user(telegram_id, text)
            logger.info(
                "Payment confirmed: tx=%s tg=%s payment_id=%s vpn=%s",
                transaction_id,
                telegram_id,
                payment_id,
                bool(vpn_url),
            )

        elif status == "canceled":
            if payment_failed and payment_id:
                try:
                    payment_failed(int(payment_id))
                except Exception as e:
                    logger.exception("payment_failed: %s", e)
            if telegram_id:
                await _notify_user(
                    telegram_id,
                    "❌ Оплата не прошла или была отменена.\n\n"
                    "Можете оформить тариф заново в разделе «💳 Тарифы».",
                )
            logger.info("Payment canceled: tx=%s tg=%s", transaction_id, telegram_id)

        elif status == "chargeback":
            logger.warning(
                "CHARGEBACK tx=%s tg=%s payment_id=%s amount=%s",
                transaction_id,
                telegram_id,
                payment_id,
                amount,
            )
            # при желании здесь можно деактивировать подписку

        else:
            logger.info("Webhook status ignored: %s tx=%s", status, transaction_id)

        # Успешный приём — всегда 200
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "status": status,
                "transactionId": transaction_id,
            },
        )

    except Exception as e:
        # Неожиданная ошибка — 500, Platega повторит (до 3 раз)
        logger.exception("Webhook handler crash tx=%s: %s", transaction_id, e)
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "internal_error"},
        )


@router.get("/webhook")
async def platega_webhook_ping():
    """Проверка, что endpoint жив (для отладки)."""
    return {"ok": True, "service": "platega-webhook"}
