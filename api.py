"""Клиент VELORA API: create-sub / revoke, с end_date."""

from __future__ import annotations

import logging
from typing import Any, Optional

import aiohttp

from config import API_URL, API_KEY

logger = logging.getLogger(__name__)


class VeloraAPIError(Exception):
    def __init__(self, message: str, status: Optional[int] = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body = body


def _headers() -> dict:
    return {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def create_vpn_subscription(
    telegram_id: int,
    plan: str = "",
    period: str = "",
    end_date: str | None = None,
) -> dict:
    if not API_KEY:
        raise VeloraAPIError("VELORA_API_KEY не задан в .env")

    payload = {
        "telegram_id": int(telegram_id),
        "plan": plan or None,
        "period": period or None,
    }
    if end_date:
        payload["end_date"] = end_date

    url = f"{API_URL}/internal/create-sub"
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload, headers=_headers()) as response:
            text = await response.text()
            try:
                data = await response.json(content_type=None)
            except Exception:
                data = {"raw": text}

            if response.status >= 400:
                logger.error("API error %s: %s", response.status, data)
                raise VeloraAPIError(
                    f"API error {response.status}",
                    status=response.status,
                    body=data,
                )

            token = data.get("token") or data.get("subscription_token")
            sub_url = (
                data.get("url")
                or data.get("subscription_url")
                or (f"{API_URL}/sub/{token}" if token else None)
            )
            if not sub_url:
                raise VeloraAPIError("API не вернул url/token", body=data)

            data["url"] = sub_url
            if token:
                data["token"] = token
            return data


async def create_subscription(telegram_id: int, plan: str = "", period: str = "") -> str:
    data = await create_vpn_subscription(telegram_id, plan=plan, period=period)
    return data["url"]


async def revoke_vpn_subscription(telegram_id: int) -> bool:
    """Отозвать доступ на API (ссылка /sub перестанет работать)."""
    if not API_KEY:
        return False
    url = f"{API_URL}/internal/revoke-sub"
    payload = {"telegram_id": int(telegram_id)}
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=_headers()) as response:
                if response.status >= 400:
                    logger.warning("revoke-sub %s", response.status)
                    return False
                return True
    except Exception as e:
        logger.warning("revoke-sub fail: %s", e)
        return False
