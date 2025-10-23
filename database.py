import asyncio
import logging
import os
import uuid
from datetime import datetime
import asyncpg
from config import load_config
from cache import prompt_cache

config = load_config()


async def add_new_user_to_db(tg_id: int, username: str = None):
    conn = None
    try:
        conn = await asyncpg.connect(config.db_path)

        # Проверяем, есть ли пользователь уже в базе
        existing_user = await conn.fetchrow(
            "SELECT * FROM public.nevesta_users WHERE tg_id = $1",
            tg_id
        )

        if existing_user:
            logging.info(f"Пользователь {tg_id} уже существует в БД.")
            return True

        session_id = str(uuid.uuid4())

        # Добавляем нового пользователя
        query = """
        INSERT INTO public.nevesta_users (tg_id, username, is_actual, message_limit, last_message_time, session_id)
        VALUES ($1, $2, TRUE, $3, $4, $5)
        RETURNING *;
        """
        new_user = await conn.fetchrow(query, tg_id, username, int(os.getenv("LIMIT_MESSAGES")), datetime.now(), session_id)

        logging.info(f"Добавлен новый пользователь: {new_user}")
        return True

    except Exception as e:
        logging.error(f"Ошибка при добавлении пользователя {tg_id}: {e}")
        return False
    finally:
        if conn:
            await conn.close()


async def get_session_id_db(tg_id: int):
    """Получает session_id по тг ид"""
    try:
        conn = await asyncpg.connect(config.db_path)
        query = "SELECT session_id FROM public.nevesta_users WHERE tg_id = $1"
        row = await conn.fetchrow(query, tg_id)
        await conn.close()
        return str(row['session_id'])

    except Exception as e:
        logging.error(f"Ошибка при получении session_id '{tg_id}': {e}")
        return None

async def get_prompt_from_db_or_cache(name: str = "main_prompt") -> str:
    """
    Получает промпт из кэша или из БД.
    """
    # Если промпт уже в кэше — возвращаем
    if name in prompt_cache:
        return prompt_cache[name]["content"]

    # Если нет — достаём из базы
    try:
        conn = await asyncpg.connect(config.db_path)
        query = "SELECT content, updated_at FROM public.nevesta_prompts WHERE name = $1"
        row = await conn.fetchrow(query, name)
        await conn.close()

        if row:
            prompt_cache[name] = {
                "content": row["content"],
                "updated_at": row["updated_at"]
            }
            return row["content"]
        else:
            logging.warning(f"Промпт '{name}' не найден в БД.")
            return None

    except Exception as e:
        logging.error(f"Ошибка при получении промпта '{name}': {e}")
        return None


async def save_message(user_id: int, role: str, message: str):
    """
    Сохраняет сообщение пользователя или бота в базу данных.
    :param user_id: Telegram ID пользователя
    :param role: 'user' или 'bot'
    :param message: текст сообщения
    """
    try:
        conn = await asyncpg.connect(config.db_path)
        await conn.execute(
            """
            INSERT INTO public.nevesta_messages (user_id, role, message, created_at)
            VALUES ($1, $2, $3, $4)
            """,
            user_id, role, message, datetime.utcnow()
        )
        await conn.close()
        return True
    except Exception as e:
        print(f"Ошибка при сохранении сообщения: {e}")
        return False

async def get_last_messages(user_id: int, limit: int = 10):
    """
    Возвращает последние сообщения пользователя и бота.
    """
    try:
        conn = await asyncpg.connect(config.db_path)
        rows = await conn.fetch(
            """
            SELECT role, message
            FROM public.nevesta_messages
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id, limit
        )
        await conn.close()
        return list(reversed(rows))
    except Exception as e:
        print(f"Ошибка при загрузке сообщений: {e}")
        return []


async def main():
    result = await get_session_id_db(696933310)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())