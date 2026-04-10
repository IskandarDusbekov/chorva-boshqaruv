from aiogram import Dispatcher

from apps.accounts.bot_handlers import router as accounts_router
from apps.dashboard.bot_handlers import router as dashboard_router


def build_dispatcher():
    dispatcher = Dispatcher()
    dispatcher.include_router(accounts_router)
    dispatcher.include_router(dashboard_router)
    return dispatcher
