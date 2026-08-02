"""Клиент VELORA API: POST /internal/create-sub"""

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


async def create_vpn_subscription(
    telegram_id: int,
    plan: str = "",
    period: str = "",
) -> dict:
    if not API_KEY:
        raise VeloraAPIError("VELORA_API_KEY не задан в .env")

    payload = {
        "telegram_id": int(telegram_id),
        "plan": plan or None,
        "period": period or None,
    }
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    url = f"{API_URL}/internal/create-sub"
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload, headers=headers) as response:
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
