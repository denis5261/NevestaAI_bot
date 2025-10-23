import asyncio
import logging
import random

from aiogram import Router, types
from bot.AI.gigachat_client import Gigachat
from bot.utils.update_cache_limit_meseges import update_user_limit, get_user_limit
from database import add_new_user_to_db, save_message

router = Router()


@router.message()
async def handle_message(message: types.Message):
    tg_id = message.from_user.id
    user = message.from_user
    giga = Gigachat()

    # Проверяем, есть ли пользователь в БД
    success = await add_new_user_to_db(user.id, user.username)

    if not success:
        await message.answer("Что-то пошло не так… попробуй позже 🙈")
        return

    # Проверяем лимит сообщений
    limit = int(await get_user_limit(tg_id))
    if limit <= 0:
        await message.answer("На сегодня лимит кончился 😅 Давай продолжим через сутки 💬")
        return

    await save_message(tg_id, "user", message.text)

    response = await giga.resp_giga(tg_id=user.id, text=message.text)

    # Фильтр на системные ответы
    if 'генеративные языковые модели' in response.lower() or 'во избежание неправильного толкования' in response.lower():
        response = random.choice([
            "Ой, даже не знаю, как ответить 😅 Давай лучше про что-то другое, ладно?",
            "Ха, вот это вопрос! Даже не знаю, как ответить 😅",
            "Слушай, сложно сказать… давай лучше про что-нибудь повеселее 😉",
            "Хмм… я сейчас немного растерялась 😅",
            "А вот это секрет 🤫"
        ])

    # ⏳ Эффект "печатает..."
    # Рассчитываем примерное время набора (0.03–0.06 сек на символ)
    typing_time = min(max(len(response) * random.uniform(0.03, 0.06), 2), 10)

    # Иногда делаем короткие "перерывы", как будто задумалась
    break_points = sorted(random.sample(range(1, int(typing_time)), k=min(2, int(typing_time)//2))) if typing_time > 4 else []

    await message.bot.send_chat_action(message.chat.id, "typing")

    elapsed = 0
    for bp in break_points:
        await asyncio.sleep(bp - elapsed)
        elapsed = bp
        # Прерываем "печать", затем снова "печатает"
        await message.bot.send_chat_action(message.chat.id, "typing")
        await asyncio.sleep(random.uniform(0.3, 0.8))

    # Оставшееся время до конца "набора"
    await asyncio.sleep(max(typing_time - elapsed, 0.5))

    await save_message(tg_id, "bot", response)

    await message.answer(response)
    # 💡 Уменьшаем лимит после успешного ответа
    await update_user_limit(tg_id, limit - 1)