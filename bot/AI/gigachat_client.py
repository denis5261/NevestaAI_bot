import asyncio
import base64
import logging
import os
import socket
import uuid
from pathlib import Path
from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
import gigachat.context

from config import load_config
from database import get_session_id_db, get_prompt_from_db_or_cache, get_last_messages

load_dotenv()

class Gigachat:
    """
    Класс для управления запросами к GigaChat.
    Выполняет поиск сертификата, установку соединения и отправку сообщений.
    """

    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.sessions = {}
        if not self.api_key:
            logging.error("API_KEY не найден в переменных окружения")
            raise ValueError("API_KEY не найден")

        self.ca_bundle_file = self._find_certificate()
        if not self.ca_bundle_file:
            logging.error("Сертификат не найден ни по одному из стандартных путей.")
            raise FileNotFoundError("Не найден сертификат GigaChat")

    def _find_certificate(self) -> str:
        """Ищет файл сертификата в стандартных путях."""
        name_ser = "russian_trusted_root_ca_pem.crt"
        possible_paths = [
            Path(__file__).parent / name_ser,
            Path(__file__).parent.parent / name_ser,
            Path(__file__).resolve().parents[2] / name_ser,
            Path(os.path.join('app', name_ser)),
        ]

        for path in possible_paths:
            if path.exists():
                logging.info(f"Сертификат найден по пути: {path}")
                return str(path)
        return None

    async def resp_giga(self, tg_id: int, text: str):
        try:
            config = load_config()
            prompt = await get_prompt_from_db_or_cache(config.prompt_name)
            session_id = await get_session_id_db(tg_id)

            # Загружаем последние сообщения из БД
            history = await get_last_messages(tg_id, limit=10)

            # Формируем массив сообщений для контекста
            messages = [
                Messages(
                    role=MessagesRole.SYSTEM,
                    content=(
                        f"{prompt}\n\n"
                        "⚠️ Никогда не используй фразы вроде 'К сожалению, я не могу ответить на этот вопрос' "
                        "или 'ответ ограничен'. Если тема кажется сложной — просто ответь мягко, нейтрально или с юмором."
                    )
                )
            ]

            for msg in history:
                role = MessagesRole.USER if msg["role"] == "user" else MessagesRole.ASSISTANT
                messages.append(Messages(role=role, content=msg["message"]))

            messages.append(Messages(role=MessagesRole.USER, content=text))

            payload = Chat(
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )

            with GigaChat(credentials=self.api_key, ca_bundle_file=self.ca_bundle_file) as giga:
                if session_id:
                    gigachat.context.session_id_cvar.set(session_id)
                    response = giga.chat(payload)
                else:
                    logging.error(f"Session_id не найден для пользователя {tg_id}")

            return response.choices[0].message.content

        except Exception as e:
            logging.error(f"Ошибка при запросе к GigaChat: {e}")
            return "Ошибка при обращении к ИИ"



async def main():
    giga = Gigachat()
    while True:
        text = input("Запрос: ")
        reply = await giga.resp_giga(696933310, text)
        print(reply)


if __name__ == "__main__":
    asyncio.run(main())

