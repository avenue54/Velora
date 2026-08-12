import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from handlers import router
from admin import router as admin_router
from database import (
    create_database,
    get_expiring_subscriptions,
    get_expiring_by_level,
    mark_subscription_reminded,
)
from config import BOT_TOKEN

load_dotenv()


async def subscription_reminder_loop(bot: Bot) -> None:
    while True:
        try:
            LEVELS = [
                (12, 1, "12 часов"),
                (6,  2, "6 часов"),
                (1,  3, "1 час"),
            ]
            for hours, level, label in LEVELS:
                try:
                    subs = get_expiring_by_level(hours=hours, level=level)
                    for sub_id, tg_id, plan, period, end_date in subs:
                        try:
                            await bot.send_message(
                                chat_id=tg_id,
                                text=(
                                    f"⏰ <b>Подписка истекает через {label}</b>\n\n"
                                    f"Тариф: <b>{plan}</b> ({period})\n"
                                    f"Истекает: <b>{end_date}</b>\n\n"
                                    "Продлите подписку в разделе «👤 Мой аккаунт» → "
                                    "«🔄 Продлить подписку», чтобы не потерять доступ."
                                ),
                            )
                            mark_subscription_reminded(sub_id, level=level)
                            print(f"Reminder L{level} sent: sub #{sub_id} → {tg_id}")
                        except Exception as e:
                            print(f"Reminder L{level} fail sub #{sub_id}: {e}")
                except Exception as e:
                    print(f"Reminder L{level} loop error: {e}")
        except Exception as e:
            print(f"Reminder loop error: {e}")

        await asyncio.sleep(1800)


async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(admin_router)

    create_database()
    print("✅ VELORA запущен")

    asyncio.create_task(subscription_reminder_loop(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())