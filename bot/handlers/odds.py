from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import dp
from database import SessionLocal
from database.crud import get_matches_by_sport, get_latest_odds_for_match


@dp.callback_query(lambda c: c.data.startswith("odds:"))
async def callback_odds(callback_query: types.CallbackQuery):
    """Обработчик сравнения коэффициентов"""
    action = callback_query.data.split(":")[1]

    if action == "compare":
        await show_matches_for_comparison(callback_query)
    elif action.startswith("match_"):
        match_id = int(action.split("_")[1])
        await show_match_odds(callback_query, match_id)


async def show_matches_for_comparison(callback_query: types.CallbackQuery):
    """Показать матчи для сравнения коэффициентов"""
    db = SessionLocal()
    try:
        sports = ["football", "basketball", "hockey", "tennis"]
        matches = []
        for sport in sports[:2]:
            sport_matches = get_matches_by_sport(db, sport, limit=5)
            matches.extend(sport_matches)

        if not matches:
            text = "📭 Пока нет доступных матчей для сравнения.\n\nПопробуйте позже или проверьте настройки парсинга."
        else:
            text = "📊 **Выберите матч для сравнения коэффициентов:**\n\n"
            for match in matches[:10]:
                text += f"⚽ {match.team_home} vs {match.team_away}\n"
                if match.start_time:
                    text += f"   📅 {match.start_time.strftime('%d.%m %H:%M')}\n"
                text += "\n"

    finally:
        db.close()

    await callback_query.message.edit_text(
        text,
        reply_markup=get_back_keyboard()
    )
    await callback_query.answer()


async def show_match_odds(callback_query: types.CallbackQuery, match_id: int):
    """Показать коэффициенты для матча"""
    db = SessionLocal()
    try:
        odds_list = get_latest_odds_for_match(db, match_id)

        if not odds_list:
            text = "📭 Коэффициенты для этого матча пока не собраны."
        else:
            text = "📊 **Коэффициенты букмекеров:**\n\n"
            for odds in odds_list:
                text += f"🏦 **{odds.bookmaker}**\n"
                text += f"   П1: {odds.outcome_home} | X: {odds.outcome_draw} | П2: {odds.outcome_away}\n\n"

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
