import asyncio
import os
import sys
from pathlib import Path

import django
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.accounts.bot_handlers import router as accounts_router
from apps.dashboard.bot_handlers import router as dashboard_router


async def main():
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise RuntimeError("BOT_TOKEN topilmadi.")

    bot = Bot(token=token)
    dispatcher = Dispatcher()
    dispatcher.include_router(accounts_router)
    dispatcher.include_router(dashboard_router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
