"""
Handler for "Матчи дня" feature
Shows popular matches with detailed information
"""
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import dp
from database import SessionLocal
from database.crud import get_matches_by_sport, get_latest_odds_for_match
from database.models import Match
from parsers.flashscore import flashscore_parser
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


@dp.callback_query(lambda c: c.data.startswith("matches:"))
async def callback_matches(callback_query: types.CallbackQuery):
    action = callback_query.data.split(":")[1]

    if action == "today":
        await show_sports_selection(callback_query)
    elif action.startswith("sport_"):
        sport = action.split("_")[1]
        await show_matches_list(callback_query, sport)
    elif action.startswith("detail_"):
        match_id = int(action.split("_")[1])
        await show_match_card(callback_query, match_id)


async def show_sports_selection(callback_query: types.CallbackQuery):
    """Show sport selection for matches of the day"""
    text = (
        "🔥 <b>Матчи дня</b>\n\n"
        "Выбери вид спорта, чтобы увидеть самые популярные матчи:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚽ Футбол", callback_data="matches:sport_football"),
            InlineKeyboardButton(text="🏀 Баскетбол", callback_data="matches:sport_basketball"),
        ],
        [
            InlineKeyboardButton(text="🎾 Теннис", callback_data="matches:sport_tennis"),
            InlineKeyboardButton(text="⚾ Бейсбол", callback_data="matches:sport_baseball"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main"),
        ],
    ])

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


async def show_matches_list(callback_query: types.CallbackQuery, sport: str):
    """Show list of popular matches for selected sport"""
    db = SessionLocal()
    try:
        # Get matches from database
        matches = get_matches_by_sport(db, sport, limit=10)

        if not matches:
            emoji = SPORT_EMOJI.get(sport, "🏟")
            text = (
                f"{emoji} <b>{SPORT_NAMES.get(sport, sport)}</b>\n\n"
                "📭 Матчи пока не загружены.\n"
                "Попробуйте позже — бот обновляет данные каждые 8 часов."
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="matches:today")]
            ])
            await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback_query.answer()
            return

        emoji = SPORT_EMOJI.get(sport, "🏟")
        text = f"{emoji} <b>Популярные матчи — {SPORT_NAMES.get(sport, sport)}</b>\n\n"

        for i, match in enumerate(matches, 1):
            # Get average odds
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
                        fav = "🤝 Равные"
                else:
                    fav = "—"
            else:
                fav = "—"

            text += f"<b>{i}. {match.team_home} vs {match.team_away}</b>\n"
            text += f"   📅 {time_str} | {match.league or '—'}\n"
            text += f"   {fav}\n\n"

        # Create buttons for each match
        buttons = []
        for match in matches:
            buttons.append([
                InlineKeyboardButton(
                    text=f"📊 {match.team_home} vs {match.team_away}",
                    callback_data=f"matches:detail_{match.id}"
                )
            ])
        buttons.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="matches:today")
        ])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    finally:
        db.close()

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


async def show_match_card(callback_query: types.CallbackQuery, match_id: int):
    """Show detailed match card"""
    db = SessionLocal()
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            await callback_query.message.edit_text("❌ Матч не найден.")
            await callback_query.answer()
            return

        # Get odds
        odds_list = get_latest_odds_for_match(db, match_id)
        odds_dicts = []
        for o in odds_list:
            odds_dicts.append({
                "bookmaker": o.bookmaker,
                "outcome_home": o.outcome_home,
                "outcome_draw": o.outcome_draw,
                "outcome_away": o.outcome_away,
            })

        analysis = match_analytics.analyze_odds(odds_dicts) if odds_dicts else {}

        # Build match card
        emoji = SPORT_EMOJI.get(match.sport, "🏟")
        time_str = match.start_time.strftime("%d.%m.%Y %H:%M") if match.start_time else "TBD"

        text = f"{emoji} <b>{match.team_home} vs {match.team_away}</b>\n\n"
        text += f"🏆 <b>Лига:</b> {match.league or '—'}\n"
        text += f"📅 <b>Время:</b> {time_str}\n\n"

        # Odds section
        if analysis.get("predictions"):
            preds = analysis["predictions"]
            text += "📊 <b>Коэффициенты:</b>\n"
            text += f"🏠 П1: <b>{preds['home']}%</b>\n"
            text += f"🤝 X: <b>{preds['draw']}%</b>\n"
            text += f"✈️ П2: <b>{preds['away']}%</b>\n\n"

            if analysis.get("favorite") == "home":
                fav = match.team_home
            else:
                fav = match.team_away
            text += f"⭐ <b>Фаворит:</b> {fav} ({analysis['confidence']}%)\n\n"

        # Best odds
        if analysis.get("best_odds"):
            text += "🏆 <b>Лучшие коэффициенты:</b>\n"
            best = analysis["best_odds"]
            if "home" in best:
                text += f"🏠 П1: <b>{best['home']['odds']}</b> ({best['home']['bookmaker']})\n"
            if "away" in best:
                text += f"✈️ П2: <b>{best['away']['odds']}</b> ({best['away']['bookmaker']})\n"
            text += "\n"

        # Value bets
        if analysis.get("value_bets"):
            text += "💰 <b>Value-ставки:</b>\n"
            for vb in analysis["value_bets"][:3]:
                text += f"  🔥 {vb['outcome']}: {vb['odds']} (+{vb['value']}%) — {vb['bookmaker']}\n"
            text += "\n"

        # All odds table
        if odds_list:
            text += "📊 <b>Все коэффициенты:</b>\n"
            text += "<code>"
            text += f"{'Букмекер':<15} {'П1':>6} {'X':>6} {'П2':>6}\n"
            text += "─" * 36 + "\n"
            for o in odds_list:
                bm = o.bookmaker[:14]
                h = f"{o.outcome_home:.2f}" if o.outcome_home and o.outcome_home > 0 else "  —"
                d = f"{o.outcome_draw:.2f}" if o.outcome_draw and o.outcome_draw > 0 else "  —"
                a = f"{o.outcome_away:.2f}" if o.outcome_away and o.outcome_away > 0 else "  —"
                text += f"{bm:<15} {h:>6} {d:>6} {a:>6}\n"
            text += "</code>\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ К списку матчей", callback_data=f"matches:sport_{match.sport}")]
        ])

    finally:
        db.close()

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()
