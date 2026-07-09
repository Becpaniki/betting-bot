from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import dp
from database import SessionLocal
from database.crud import get_unnotified_value_bets


@dp.callback_query(lambda c: c.data.startswith("value:"))
async def callback_value(callback_query: types.CallbackQuery):
    """Обработчик value-ставок"""
    action = callback_query.data.split(":")[1]

    if action == "show":
        await show_value_bets(callback_query)


async def show_value_bets(callback_query: types.CallbackQuery):
    """Показать текущие value-ставки"""
    db = SessionLocal()
    try:
        value_bets = get_unnotified_value_bets(db, min_value=0.03)

        if not value_bets:
            text = (
                "💰 **Value-ставки не найдены**\n\n"
                "Сейчас нет предложений с завышенными коэффициентами.\n"
                "Бот проверяет коэффициенты каждые 15 минут.\n\n"
                "💡 **Совет:** Настройте уведомления, чтобы не пропустить выгодные предложения!"
            )
        else:
            text = "💰 **Value-ставки (завышенные коэффициенты):**\n\n"

            for bet in value_bets[:10]:
                if bet.value_percentage >= 15:
                    level = "🔥 РЕДКАЯ"
                elif bet.value_percentage >= 10:
                    level = "⭐ ОТЛИЧНАЯ"
                elif bet.value_percentage >= 5:
                    level = "✅ ХОРОШАЯ"
                else:
                    level = "📊 ЕСТЬ"

                outcome_text = {
                    "home": f"П1 ({bet.match.team_home})",
                    "draw": "X (Ничья)",
                    "away": f"П2 ({bet.match.team_away})"
                }.get(bet.outcome, bet.outcome)

                text += f"{level} **{bet.value_percentage:.1f}%**\n"
                text += f"⚽ {bet.match.team_home} vs {bet.match.team_away}\n"
                text += f"   🎯 {outcome_text}\n"
                text += f"   💵 Кэф: {bet.odds} (справедливый: {bet.fair_odds:.2f})\n"
                text += f"   🏦 Букмекер: {bet.bookmaker}\n\n"

    finally:
        db.close()

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
