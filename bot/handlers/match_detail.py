from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import dp
from database import SessionLocal
from database.crud import get_latest_odds_for_match
from database.models import Match
from parsers.match_analytics import match_analytics
from analytics.value_finder import ValueFinder

SPORT_EMOJI = {
    "football": "⚽",
    "basketball": "🏀",
    "hockey": "🏒",
    "tennis": "🎾",
    "esports": "🎮",
}

value_finder = ValueFinder()


@dp.callback_query(lambda c: c.data.startswith("match_detail:"))
async def callback_match_detail(callback_query: types.CallbackQuery):
    match_id = int(callback_query.data.split(":")[1])
    await show_match_detail(callback_query, match_id)


async def show_match_detail(callback_query: types.CallbackQuery, match_id: int):
    db = SessionLocal()
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            await callback_query.message.edit_text("❌ Матч не найден.")
            await callback_query.answer()
            return

        odds_list = get_latest_odds_for_match(db, match_id)

        if not odds_list:
            text = format_match_header(match)
            text += "\n📭 <b>Коэффициенты пока не собраны.</b>"
            keyboard = get_detail_back_keyboard(match.sport)
            await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback_query.answer()
            return

        odds_dicts = []
        for o in odds_list:
            odds_dicts.append({
                "bookmaker": o.bookmaker,
                "outcome_home": o.outcome_home,
                "outcome_draw": o.outcome_draw,
                "outcome_away": o.outcome_away,
            })

        analysis = match_analytics.analyze_odds(odds_dicts)

        text = format_match_header(match)
        text += format_analysis(match, analysis)
        text += format_all_odds(odds_list, match)

        keyboard = get_detail_back_keyboard(match.sport)

    finally:
        db.close()

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


def format_match_header(match: Match) -> str:
    emoji = SPORT_EMOJI.get(match.sport, "🏟")
    time_str = match.start_time.strftime("%d.%m.%Y %H:%M") if match.start_time else "TBD"
    return (
        f"{emoji} <b>{match.team_home} vs {match.team_away}</b>\n"
        f"📅 {time_str}\n"
        f"🏆 {match.league or '—'}\n\n"
    )


def format_analysis(match: Match, analysis: dict) -> str:
    text = ""

    if analysis.get("predictions"):
        preds = analysis["predictions"]
        text += "📊 <b>Прогноз (по коэффициентам):</b>\n"
        text += f"🏠 {match.team_home}: <b>{preds['home']}%</b>\n"
        text += f"🤝 Ничья: <b>{preds['draw']}%</b>\n"
        text += f"✈️ {match.team_away}: <b>{preds['away']}%</b>\n\n"

        if analysis.get("favorite") == "home":
            fav = match.team_home
        else:
            fav = match.team_away
        text += f"⭐ <b>Фаворит:</b> {fav} ({analysis['confidence']}%)\n\n"

    if analysis.get("margin"):
        margin = analysis["margin"]
        margin_emoji = "🟢" if margin < 5 else "🟡" if margin < 10 else "🔴"
        text += f"{margin_emoji} <b>Маржа:</b> {margin:.1f}%\n\n"

    if analysis.get("best_odds"):
        text += "🏆 <b>Лучшие коэффициенты:</b>\n"
        best = analysis["best_odds"]
        if "home" in best:
            text += f"🏠 П1: <b>{best['home']['odds']}</b> ({best['home']['bookmaker']})\n"
        if "draw" in best and best["draw"]:
            text += f"🤝 X: <b>{best['draw']['odds']}</b> ({best['draw']['bookmaker']})\n"
        if "away" in best:
            text += f"✈️ П2: <b>{best['away']['odds']}</b> ({best['away']['bookmaker']})\n"
        text += "\n"

    if analysis.get("value_bets"):
        text += "💰 <b>Value-ставки:</b>\n"
        for vb in analysis["value_bets"][:3]:
            text += f"  🔥 {vb['outcome']}: {vb['odds']} (+{vb['value']}%) — {vb['bookmaker']}\n"
        text += "\n"

    return text


def format_all_odds(odds_list, match: Match) -> str:
    text = "📊 <b>Все коэффициенты:</b>\n"
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
    return text


def get_detail_back_keyboard(sport: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ К списку матчей", callback_data=f"sport:{sport}")]
    ])
    return keyboard
