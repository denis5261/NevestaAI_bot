import os
from aiogram import Dispatcher
from bot.handlers import handlers_routers


def register_all_routers(dp: Dispatcher):
    all_routers = (
        handlers_routers
        #keyboards_routers
    )
    for router in all_routers:
        dp.include_router(router)