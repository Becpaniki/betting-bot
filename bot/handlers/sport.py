from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import dp
from database import SessionLocal
from database.crud import get_matches_by_sport, get_latest_odds_for_match
from analytics.value_finder import ValueFinder
from parsers.match_analytics import match_analytics

SPORT_EMOJI = {
    "football": "⚽",
    "basketball": "🏀",
    "tennis": "🎾",
    "baseball": "⚾",
}

SPORT_NAMES = {
    "football": "Футбол",
    "basketball": "Баскетбол",
    "tennis": "Теннис",
    "baseball": "Бейсбол",
}


@dp.callback_query(lambda c: c.data.startswith("sport:"))
async def callback_sport(callback_query: types.CallbackQuery):
    action = callback_query.data.split(":")[1]

    if action == "all":
        await show_all_sports(callback_query)
    elif action in SPORT_NAMES:
        await show_matches_by_sport(callback_query, action)


async def show_all_sports(callback_query: types.CallbackQuery):
    text = (
        "🏆 <b>Выбери вид спорта:</b>\n\n"
        "Нажми на кнопку, чтобы увидеть актуальные матчи с коэффициентами."
    )
    await callback_query.message.edit_text(text, reply_markup=get_sports_list_keyboard())
    await callback_query.answer()


async def show_matches_by_sport(callback_query: types.CallbackQuery, sport: str):
    db = SessionLocal()
    try:
        matches = get_matches_by_sport(db, sport, limit=10)

        if not matches:
            emoji = SPORT_EMOJI.get(sport, "🏟")
            text = (
                f"{emoji} <b>{SPORT_NAMES.get(sport, sport)}</b>\n\n"
                "📭 Матчи пока не загружены.\n"
                "Попробуйте позже — бот обновляет данные каждые 15 минут."
            )
            await callback_query.message.edit_text(text, reply_markup=get_back_keyboard())
            await callback_query.answer()
            return

        emoji = SPORT_EMOJI.get(sport, "🏟")
        text = f"{emoji} <b>{SPORT_NAMES.get(sport, sport)}</b> — ближайшие матчи:\n\n"

        for i, match in enumerate(matches, 1):
            odds_list = get_latest_odds_for_match(db, match.id)

            time_str = ""
            if match.start_time:
                time_str = match.start_time.strftime("%d.%m %H:%M")

            if odds_list:
                home_odds = [o.outcome_home for o in odds_list if o.outcome_home and o.outcome_home > 0]
                away_odds = [o.outcome_away for o in odds_list if o.outcome_away and o.outcome_away > 0]

                avg_home = sum(home_odds) / len(home_odds) if home_odds else 0
                avg_away = sum(away_odds) / len(away_odds) if away_odds else 0

                if avg_home > 0 and avg_away > 0:
                    if avg_home < avg_away:
                        fav = f"⭐ {match.team_home}"
                    elif avg_away < avg_home:
                        fav = f"⭐ {match.team_away}"
                    else:
                        fav = "🤝 Равные шансы"
                else:
                    fav = "—"

                odds_text = f"Кэф: {avg_home:.2f} | {avg_away:.2f}"
            else:
                fav = "—"
                odds_text = "Кэф: —"

            text += f"<b>{i}. {match.team_home} vs {match.team_away}</b>\n"
            text += f"   📅 {time_str}  |  🏆 {match.league or '—'}\n"
            text += f"   📊 {odds_text}  |  {fav}\n\n"

        keyboard = get_matches_keyboard(matches, sport)

    finally:
        db.close()

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


def get_matches_keyboard(matches, sport: str) -> InlineKeyboardMarkup:
    buttons = []
    for match in matches:
        buttons.append([
            InlineKeyboardButton(
                text=f"📊 {match.team_home} vs {match.team_away}",
                callback_data=f"match_detail:{match.id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="sport:all")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_sports_list_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚽ Футбол", callback_data="sport:football"),
            InlineKeyboardButton(text="🏀 Баскетбол", callback_data="sport:basketball"),
        ],
        [
            InlineKeyboardButton(text="🎾 Теннис", callback_data="sport:tennis"),
            InlineKeyboardButton(text="⚾ Бейсбол", callback_data="sport:baseball"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main"),
        ],
    ])
    return keyboard


def get_back_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="sport:all")]
    ])
    return keyboard
