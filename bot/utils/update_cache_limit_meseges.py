import os

import asyncpg
import asyncio
import datetime
import logging
from config import load_config
from cache import user_limits_cache

config = load_config()

async def get_user_limit(tg_id: int) -> int:
    """Получает лимит сообщений из БД с кэшированием и автообновлением"""
    now = datetime.datetime.now()

    try:
        # Проверяем лимит в БД (всегда приоритетно)
        conn = await asyncpg.connect(config.db_path)
        row = await conn.fetchrow(
            "SELECT message_limit, last_message_time FROM public.nevesta_users WHERE tg_id = $1",
            tg_id
        )
        await conn.close()

        if not row:
            logging.warning(f"Пользователь {tg_id} не найден в БД при запросе лимита")
            return 0

        db_limit = int(row["message_limit"])
        last_update = row["last_message_time"]

        # Проверяем, не прошло ли 24 часа (или временно 60 сек)
        if (now - last_update).total_seconds() >= 86400:
            reset_limit = int(os.getenv("LIMIT_MESSAGES", 20))
            await update_user_limit(tg_id, reset_limit)
            user_limits_cache[tg_id] = {"limit": reset_limit, "last_update": now}
            return reset_limit

        # Кэшируем актуальное значение из БД
        user_limits_cache[tg_id] = {"limit": db_limit, "last_update": now}
        return db_limit

    except Exception as e:
        logging.error(f"Ошибка при получении лимита пользователя {tg_id}: {e}")

        # fallback — если нет связи с БД, возвращаем значение из кэша
        if tg_id in user_limits_cache:
            cached = user_limits_cache[tg_id]
            return cached["limit"]

        return 0


async def update_user_limit(tg_id: int, new_limit: int):
    """Обновляет лимит пользователя и сохраняет в кэш + БД"""
    now = datetime.datetime.now()

    # Обновляем в кэше
    user_limits_cache[tg_id] = {
        "limit": new_limit,
        "last_update": now
    }

    try:
        conn = await asyncpg.connect(config.db_path)
        await conn.execute(
            """
            UPDATE public.nevesta_users
            SET message_limit = $1, last_message_time = $2
            WHERE tg_id = $3
            """,
            new_limit, now, tg_id
        )
        await conn.close()
    except Exception as e:
        logging.error(f"Ошибка при обновлении лимита {tg_id}: {e}")