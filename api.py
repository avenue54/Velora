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


async def create_vpn_subscription(telegram_id: int, plan: str = "", period: str = ""):
    """Создаёт подписку + токен + WireGuard конфиг (новый API)"""
    url = f"{API_URL}/internal/create-sub"
    
    payload = {
        "telegram_id": int(telegram_id),
        "plan": plan or "Plus",
        "period": period or "1 месяц",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            }, json=payload) as response:
                
                if response.status != 200:
                    raise VeloraAPIError(f"API error {response.status}")

                data = await response.json()
                
                sub_url = data.get("url") or data.get("subscription_url")
                
                if not sub_url:
                    raise VeloraAPIError("API не вернул URL конфига")

                return {"url": sub_url}

    except Exception as e:
        logger.error(f"VeloraAPIError: {e}")
        raise VeloraAPIError(str(e))


async def create_subscription(telegram_id: int, plan: str = "", period: str = "") -> str:
    data = await create_vpn_subscription(telegram_id, plan=plan, period=period)
    return data["url"]
