from aiogram import Router, types
from aiogram.filters import CommandStart
from bot.AI.gigachat_client import Gigachat
from database import add_new_user_to_db

router = Router()

giga = Gigachat()


@router.message(CommandStart())
async def start_handler(message: types.Message):
    """
    Обрабатывает команду /start
    """
    giga = Gigachat()
    user = message.from_user
    success = await add_new_user_to_db(user.id, user.username)
    if success:
        user_name = message.from_user.first_name or "друг"
        welcome_text = f"{await giga.resp_giga(tg_id=user.id, text=f'Поздаровайся со мной меня зовут {user_name}')}"
        await message.answer(welcome_text)
    else:
        await message.answer("Не могу пока что ответить 😓, Извини!")


