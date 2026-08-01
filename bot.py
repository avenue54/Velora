import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from handlers import router
from database import (
    create_database,
    get_expiring_subscriptions,
    mark_subscription_reminded
)
from admin import router as admin_router
from config import BOT_TOKEN

load_dotenv()

BOT_TOKEN = os.getenv("VELORA_BOT_TOKEN")


async def subscription_reminder_loop(bot: Bot):
    """Раз в час проверяет подписки, истекающие в ближайшие 48 часов."""
    while True:
        try:
            expiring = get_expiring_subscriptions(hours=48)
            for sub_id, tg_id, plan, period, end_date in expiring:
                try:
                    await bot.send_message(
                        chat_id=tg_id,
                        text=(
                            "⏰ <b>Напоминание о подписке VELORA</b>\n\n"
                            f"Ваша подписка <b>{plan}</b> ({period}) "
                            f"истекает <b>{end_date}</b>.\n\n"
                            "Продлите её заранее в разделе «👤 Мой аккаунт» → "
                            "«🔄 Продлить подписку», чтобы не потерять доступ."
                        )
                    )
                    mark_subscription_reminded(sub_id)
                    print(f"Reminder sent: sub #{sub_id} → {tg_id}")
                except Exception as e:
                    print(f"Reminder fail sub #{sub_id}: {e}")
        except Exception as e:
            print(f"Reminder loop error: {e}")

        await asyncio.sleep(3600)  # каждый час


async def main():

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    dp = Dispatcher()

    dp.include_router(router)
    dp.include_router(admin_router)
    create_database()
    print("✅ VELORA запущен")

    # Фоновые напоминания за 48 часов
    asyncio.create_task(subscription_reminder_loop(bot))

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
