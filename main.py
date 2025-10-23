from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.utils.update_cache_prompt import refresh_prompt_cache
from config import load_config, setup_logging
from bot.utils.register_all_routers import register_all_routers
import asyncio
import logging


async def main():

    setup_logging()

    config = load_config()

    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    register_all_routers(dp)

    logging.info("🚀 Бот запущен")
    cache_task = asyncio.create_task(refresh_prompt_cache(interval=int(config.interval_update_cache)))
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user.")
