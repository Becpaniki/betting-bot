import logging
from aiogram import executor

from bot import dp
from database import init_db

# Импортируем все обработчики
from bot.handlers import start, odds, value, settings, predictions


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def on_startup(dispatcher):
    """Действия при запуске бота"""
    logger.info("Bot starting up...")

    # Инициализируем базу данных
    init_db()
    logger.info("Database initialized")


async def on_shutdown(dispatcher):
    """Действия при остановке бота"""
    logger.info("Bot shutting down...")


if __name__ == '__main__':
    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )
