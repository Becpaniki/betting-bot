"""
Telegram-бот для анализа ставок на спорт

Основные функции:
- Сравнение коэффициентов разных букмекеров
- Поиск value-ставок (завышенных коэффициентов)
- Автоматические уведомления о выгодных предложениях
"""

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot import dp, bot
from database import init_db
from config import config
from fetcher import fetch_and_save_odds

# Импортируем обработчики
from bot.handlers import start, sport, match_detail, odds, value, settings, predictions

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_fetch():
    """Периодическая загрузка коэффициентов"""
    try:
        logger.info("Scheduled fetch started...")
        matches, odds = await fetch_and_save_odds()
        logger.info(f"Scheduled fetch complete: {matches} matches, {odds} odds")
    except Exception as e:
        logger.error(f"Scheduled fetch error: {e}")


async def main():
    """Основная функция запуска бота"""
    logger.info("=" * 50)
    logger.info("Betting Bot starting up...")
    logger.info("=" * 50)

    # Инициализируем базу данных
    init_db()
    logger.info("Database initialized")

    # Проверяем токен бота
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Please set it in .env file or environment variable.")
        return

    if not config.ODDS_API_KEY:
        logger.warning("ODDS_API_KEY not set! Real odds will not be fetched.")
    else:
        # Первый запуск загрузки
        logger.info("Fetching initial odds from API...")
        await scheduled_fetch()

        # Периодическая загрузка каждые 15 минут
        scheduler.add_job(scheduled_fetch, 'interval', minutes=config.PARSE_INTERVAL_MINUTES)
        scheduler.start()
        logger.info(f"Scheduler started: fetching every {config.PARSE_INTERVAL_MINUTES} minutes")

    logger.info(f"Value thresholds: {config.VALUE_THRESHOLD_GOOD*100}% / {config.VALUE_THRESHOLD_GREAT*100}% / {config.VALUE_THRESHOLD_RARE*100}%")
    logger.info("=" * 50)
    logger.info("Bot is ready!")
    logger.info("=" * 50)

    # Запускаем polling
    try:
        await dp.start_polling(bot, skip_updates=False)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
