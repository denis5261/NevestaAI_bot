import logging
import sys
from dataclasses import dataclass
from logging.handlers import TimedRotatingFileHandler

from dotenv import load_dotenv
import os

load_dotenv()


@dataclass
class Config:
    bot_token: str
    db_path: str
    interval_update_cache: str
    prompt_name: str


def load_config() -> Config:
    return Config(
        bot_token=os.getenv("BOT_TOKEN"),
        db_path=os.getenv("DB_PATH", "mydb1.db"),
        interval_update_cache=os.getenv("UPDATE_CACHE"),
        prompt_name=os.getenv("PROMPT_NAME")
    )


def setup_logging():
    """Настраивает продвинутое логирование с ротацией файлов."""
    # Определяем формат логов
    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

    # Получаем корневой логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # --- Настройка вывода в консоль ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)

    # --- Настройка вывода в файл с ротацией ---
    # Создаем папку для логов, если ее нет
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Настраиваем файловый обработчик с ежедневной ротацией
    # backupCount=7 означает, что будут храниться логи за последние 7 дней
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(logs_dir, "bot.log"),
        when="D",  # 'D' - ротация по дням
        interval=1,  # интервал - 1 день
        backupCount=7,  # хранить 7 старых файлов
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)

    logging.info("Logging configured successfully with console and file output.")
