from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import dp


@dp.callback_query(lambda c: c.data.startswith("predictions:"))
async def callback_predictions(callback_query: types.CallbackQuery):
    """Обработчик прогнозов"""
    action = callback_query.data.split(":")[1]

    if action == "show":
        await show_predictions(callback_query)


async def show_predictions(callback_query: types.CallbackQuery):
    """Показать прогнозы экспертов"""
    text = (
        "🔮 **Прогнозы экспертов:**\n\n"
        "Раздел в разработке! 🚧\n\n"
        "Скоро здесь будут:\n"
        "• Прогнозы с Flashscore\n"
        "• Аналитика с SofaScore\n"
        "• Экспертные мнения\n\n"
        "💡 Пока что используйте раздел **Value-ставки** для поиска выгодных предложений!"
    )

    await callback_query.message.edit_text(
        text,
        reply_markup=get_back_keyboard()
    )
    await callback_query.answer()


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура возврата"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")]
    ])
    return keyboard
