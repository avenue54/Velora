"""
platega.py — клиент Platega API + разбор webhook.

Документация: https://docs.platega.io
Base: https://app.platega.io
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

import aiohttp

from config import PLATEGA_MERCHANT_ID, PLATEGA_SECRET, PLATEGA_API_URL

logger = logging.getLogger(__name__)


class PlategaError(Exception):
    def __init__(self, message: str, status: Optional[int] = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body = body


def parse_amount_rub(amount_str: str) -> float:
    """'129 ₽' / '129 руб' / '129' → 129.0"""
    if amount_str is None:
        raise PlategaError("Пустая сумма")
    cleaned = re.sub(r"[^\d.,]", "", str(amount_str).replace(",", "."))
    if not cleaned:
        raise PlategaError(f"Не удалось разобрать сумму: {amount_str!r}")
    return float(cleaned)


async def create_payment_link(
    *,
    amount_rub: float,
    description: str,
    payload: str,
    payment_method: int = 2,
    return_url: str = "https://t.me/Velora_news",
    failed_url: str = "https://t.me/Velora_news",
) -> dict:
    """
    Создаёт транзакцию в Platega.

    payment_method:
      2  — СБП QR
      11 — Карты
      12 — Международный эквайринг
      13 — Крипта

    Возвращает dict с ключами:
      transaction_id, redirect, status, raw
    """
    if not PLATEGA_MERCHANT_ID or not PLATEGA_SECRET:
        raise PlategaError("PLATEGA_MERCHANT_ID / PLATEGA_SECRET не заданы в .env")

    url = f"{PLATEGA_API_URL.rstrip('/')}/transaction/process"
    headers = {
        "Content-Type": "application/json",
        "X-MerchantId": PLATEGA_MERCHANT_ID,
        "X-Secret": PLATEGA_SECRET,
    }
    body = {
        "paymentMethod": payment_method,
        "paymentDetails": {
            "amount": amount_rub,
            "currency": "RUB",
        },
        "description": description[:200],
        "return": return_url,
        "failedUrl": failed_url,
        "payload": payload,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body, headers=headers, timeout=20) as resp:
                text = await resp.text()
                if resp.status != 200:
                    logger.error("Platega create error %s: %s", resp.status, text)
                    raise PlategaError(
                        f"Platega API error {resp.status}",
                        status=resp.status,
                        body=text,
                    )
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    raise PlategaError("Platega вернула не-JSON", status=resp.status, body=text)

                transaction_id = data.get("transactionId") or data.get("id")
                redirect = data.get("redirect")
                if not transaction_id or not redirect:
                    raise PlategaError(
                        "Platega не вернула transactionId/redirect",
                        status=resp.status,
                        body=data,
                    )
                return {
                    "transaction_id": str(transaction_id),
                    "redirect": redirect,
                    "status": data.get("status", "PENDING"),
                    "raw": data,
                }
    except PlategaError:
        raise
    except aiohttp.ClientError as e:
        logger.exception("Platega network error")
        raise PlategaError(f"Сеть Platega: {e}") from e


async def get_transaction_status(transaction_id: str) -> dict:
    """GET /transaction/{id} — статус платежа."""
    if not PLATEGA_MERCHANT_ID or not PLATEGA_SECRET:
        raise PlategaError("PLATEGA_MERCHANT_ID / PLATEGA_SECRET не заданы")

    url = f"{PLATEGA_API_URL.rstrip('/')}/transaction/{transaction_id}"
    headers = {
        "X-MerchantId": PLATEGA_MERCHANT_ID,
        "X-Secret": PLATEGA_SECRET,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as resp:
                text = await resp.text()
                if resp.status != 200:
                    raise PlategaError(
                        f"Status API error {resp.status}",
                        status=resp.status,
                        body=text,
                    )
                return await resp.json(content_type=None)
    except PlategaError:
        raise
    except aiohttp.ClientError as e:
        raise PlategaError(f"Сеть Platega: {e}") from e


def verify_webhook_headers(merchant_id: Optional[str], secret: Optional[str]) -> bool:
    """Проверка заголовков webhook от Platega."""
    if not PLATEGA_MERCHANT_ID or not PLATEGA_SECRET:
        return False
    if not merchant_id or not secret:
        return False
    return (
        merchant_id.strip() == PLATEGA_MERCHANT_ID.strip()
        and secret.strip() == PLATEGA_SECRET.strip()
    )


def normalize_webhook_status(raw_status: Any) -> str:
    """
    Приводит статус webhook к внутреннему:
      confirmed | canceled | chargeback | pending | unknown
    """
    if raw_status is None:
        return "unknown"
    s = str(raw_status).strip().upper()
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
    }
    # числовые статусы из доки: 7=CONFIRMED, 6=CANCELED, 9=CHARGEBACKED, 1=PENDING
    numeric = {
        "7": "confirmed",
        "6": "canceled",
        "9": "chargeback",
        "1": "pending",
    }
    if s in mapping:
        return mapping[s]
    if s in numeric:
        return numeric[s]
    return "unknown"
