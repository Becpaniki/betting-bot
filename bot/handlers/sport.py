from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import dp
from database import SessionLocal
from database.crud import get_matches_by_sport, get_latest_odds_for_match

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
        await show_sports_overview(callback_query)
    elif action in SPORT_NAMES:
        await show_sport_matches(callback_query, action)


async def show_sports_overview(callback_query: types.CallbackQuery):
    """Show overview of all sports with match counts"""
    db = SessionLocal()
    try:
        text = "🏆 <b>Доступные виды спорта</b>\n\n"

        buttons = []
        for sport_key, sport_name in SPORT_NAMES.items():
            emoji = SPORT_EMOJI.get(sport_key, "🏟")
            matches = get_matches_by_sport(db, sport_key, limit=100)
            count = len(matches)

            if count > 0:
                text += f"{emoji} <b>{sport_name}</b> — {count} матчей\n"
                buttons.append([
                    InlineKeyboardButton(
                        text=f"{emoji} {sport_name} ({count})",
                        callback_data=f"sport:{sport_key}"
                    )
                ])
            else:
                text += f"{emoji} <b>{sport_name}</b> — нет данных\n"

        text += "\nВыбери вид спорта для подробного списка."

        if buttons:
            buttons.append([
                InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")
            ])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")]
            ])

    finally:
        db.close()

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


async def show_sport_matches(callback_query: types.CallbackQuery, sport: str):
    """Show compact list of matches for a specific sport"""
    db = SessionLocal()
    try:
        matches = get_matches_by_sport(db, sport, limit=15)

        if not matches:
            emoji = SPORT_EMOJI.get(sport, "🏟")
            text = (
                f"{emoji} <b>{SPORT_NAMES.get(sport, sport)}</b>\n\n"
                "📭 Матчи пока не загружены.\n"
                "Бот обновляет данные каждые 8 часов."
            )
            await callback_query.message.edit_text(text, reply_markup=get_back_keyboard())
            await callback_query.answer()
            return

        emoji = SPORT_EMOJI.get(sport, "🏟")
        text = f"{emoji} <b>{SPORT_NAMES.get(sport, sport)}</b> — {len(matches)} матчей\n\n"

        for i, match in enumerate(matches, 1):
            time_str = ""
            if match.start_time:
                time_str = match.start_time.strftime("%d.%m %H:%M")

            odds_list = get_latest_odds_for_match(db, match.id)

            if odds_list:
                home_odds = [o.outcome_home for o in odds_list if o.outcome_home and o.outcome_home > 0]
                away_odds = [o.outcome_away for o in odds_list if o.outcome_away and o.outcome_away > 0]

                avg_home = sum(home_odds) / len(home_odds) if home_odds else 0
                avg_away = sum(away_odds) / len(away_odds) if away_odds else 0

                odds_text = f"{avg_home:.2f} | {avg_away:.2f}" if avg_home and avg_away else "—"
            else:
                odds_text = "—"

            text += f"<b>{i}.</b> {match.team_home} — {match.team_away}\n"
            text += f"   📅 {time_str} | {match.league or '—'} | {odds_text}\n"

        buttons = []
        for match in matches:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{match.team_home} vs {match.team_away}",
                    callback_data=f"match_detail:{match.id}"
                )
            ])
        buttons.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="sport:all")
        ])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    finally:
        db.close()

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


def get_back_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="sport:all")]
    ])
    return keyboard
