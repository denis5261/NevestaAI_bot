import asyncio
import logging

import asyncpg

from cache import prompt_cache
from config import load_config

config = load_config()


async def refresh_prompt_cache(interval: int = 600):
    """
    Периодически обновляет кэш только выбранного промпта из config.prompt_config.
    interval — интервал обновления в секундах.
    """
    prompt_name = config.prompt_name  # имя нужного промпта из конфига

    while True:
        try:
            conn = await asyncpg.connect(config.db_path)
            row = await conn.fetchrow(
                "SELECT name, content, updated_at FROM public.nevesta_prompts WHERE name = $1",
                prompt_name
            )
            await conn.close()

            if row:
                cached = prompt_cache.get(row["name"])
                if not cached or cached["updated_at"] < row["updated_at"]:
                    prompt_cache[row["name"]] = {
                        "content": row["content"],
                        "updated_at": row["updated_at"]
                    }
                    logging.info(f"Промпт '{row['name']}' обновлён в кэше.")
            else:
                logging.warning(f"Промпт '{prompt_name}' не найден в БД.")

        except Exception as e:
            logging.error(f"Ошибка при обновлении кэша промпта '{prompt_name}': {e}")

        await asyncio.sleep(interval)