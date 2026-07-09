from aiogram import types
from aiogram.filters import CommandStart
import logging

from bot import dp
from bot.keyboards.inline import get_main_menu_keyboard
from database import SessionLocal
from database.crud import get_user, create_user

logger = logging.getLogger(__name__)


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    logger.info(f"Received /start from user {message.from_user.id}")

    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Создаем или получаем пользователя
    db = SessionLocal()
    try:
        user = get_user(db, telegram_id)
        if not user:
            user = create_user(db, telegram_id, username, first_name)
            logger.info(f"Created new user: {telegram_id}")
    finally:
        db.close()

    welcome_text = (
        f"👋 Привет, {first_name}!\n\n"
        "Я - бот для анализа ставок на спорт.\n"
        "Показываю актуальные матчи с коэффициентами букмекеров.\n\n"
        "Нажми кнопку ниже, чтобы увидеть матчи дня 👇"
    )

    keyboard = get_main_menu_keyboard()

    logger.info(f"Sending welcome message to {telegram_id}")
    await message.answer(welcome_text, reply_markup=keyboard)
    logger.info(f"Message sent successfully")


@dp.callback_query(lambda c: c.data == "menu:main")
async def callback_main_menu(callback_query: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback_query.message.edit_text(
        "Выбери действие из меню 👇",
        reply_markup=get_main_menu_keyboard()
    )
    await callback_query.answer()
