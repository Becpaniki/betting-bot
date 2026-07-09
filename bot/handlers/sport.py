from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import dp
from database import SessionLocal
from database.crud import get_matches_by_sport, get_latest_odds_for_match
from parsers.championat import championat_parser

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

# Championat tournament mapping
CHAMPIONAT_TOURNAMENTS = {
    "football": [
        ("worldcup", "ЧМ-2026"),
        ("rpl", "РПЛ"),
        ("epl", "АПЛ"),
        ("laliga", "Ла Лига"),
        ("champions", "Лига чемпионов"),
    ],
    "basketball": [],
    "tennis": [],
    "baseball": [],
}


@dp.callback_query(lambda c: c.data.startswith("sport:"))
async def callback_sport(callback_query: types.CallbackQuery):
    action = callback_query.data.split(":")[1]

    if action == "all":
        await show_sports_overview(callback_query)
    elif action.startswith("champ_"):
        tournament = action.split("_", 1)[1]
        await show_championat_matches(callback_query, tournament)
    elif action in SPORT_NAMES:
        await show_sport_matches(callback_query, action)


async def show_sports_overview(callback_query: types.CallbackQuery):
    """Show overview of all sports with data from Championat"""
    text = "🏆 <b>Доступные виды спорта</b>\n\n"

    buttons = []

    # Football with Championat data
    buttons.append([
        InlineKeyboardButton(text="⚽ Футбол (Чемпионат)", callback_data="sport:football_champ")
    ])

    # Other sports from database
    db = SessionLocal()
    try:
        for sport_key, sport_name in SPORT_NAMES.items():
            if sport_key == "football":
                continue
            emoji = SPORT_EMOJI.get(sport_key, "🏟")
            matches = get_matches_by_sport(db, sport_key, limit=100)
            count = len(matches)
            if count > 0:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"{emoji} {sport_name} ({count} матчей)",
                        callback_data=f"sport:{sport_key}"
                    )
                ])
    finally:
        db.close()

    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


async def show_sport_matches(callback_query: types.CallbackQuery, sport: str):
    """Show compact list of matches for non-football sports"""
    db = SessionLocal()
    try:
        matches = get_matches_by_sport(db, sport, limit=15)

        if not matches:
            emoji = SPORT_EMOJI.get(sport, "🏟")
            text = f"{emoji} <b>{SPORT_NAMES.get(sport, sport)}</b>\n\n📭 Матчи пока не загружены."
            await callback_query.message.edit_text(text, reply_markup=get_back_keyboard())
            await callback_query.answer()
            return

        emoji = SPORT_EMOJI.get(sport, "🏟")
        text = f"{emoji} <b>{SPORT_NAMES.get(sport, sport)}</b> — {len(matches)} матчей\n\n"

        for i, match in enumerate(matches, 1):
            time_str = match.start_time.strftime("%d.%m %H:%M") if match.start_time else "—"
            text += f"<b>{i}.</b> {match.team_home} — {match.team_away}\n"
            text += f"   📅 {time_str} | {match.league or '—'}\n"

        buttons = []
        for match in matches:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{match.team_home} vs {match.team_away}",
                    callback_data=f"match_detail:{match.id}"
                )
            ])
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="sport:all")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    finally:
        db.close()

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


async def show_championat_tournaments(callback_query: types.CallbackQuery):
    """Show Championat tournaments for football"""
    text = "⚽ <b>Футбол — Чемпионат</b>\n\nВыбери турнир:\n"

    buttons = []
    for key, name in CHAMPIONAT_TOURNAMENTS["football"]:
        buttons.append([
            InlineKeyboardButton(text=f"🏆 {name}", callback_data=f"sport:champ_{key}")
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="sport:all")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


async def show_championat_matches(callback_query: types.CallbackQuery, tournament: str):
    """Show matches from Championat.com"""
    if tournament == "football_champ":
        await show_championat_tournaments(callback_query)
        return

    # Get matches from Championat
    matches = await championat_parser.get_calendar(tournament)

    if not matches:
        text = "📭 Матчи не найдены на Championat.com\n\nПопробуйте другой турнир."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="sport:football_champ")]
        ])
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback_query.answer()
        return

    tournament_names = dict(CHAMPIONAT_TOURNAMENTS["football"])
    name = tournament_names.get(tournament, tournament)

    text = f"⚽ <b>{name}</b> — Championat.com\n\n"

    for i, match in enumerate(matches[:10], 1):
        time_str = ""
        if match.get("start_time"):
            try:
                dt = datetime.fromisoformat(match["start_time"].replace("Z", "+00:00"))
                time_str = dt.strftime("%d.%m %H:%M")
            except:
                time_str = match["start_time"][:10]

        status = match.get("status", "")
        status_text = f" | {status}" if status else ""

        text += f"<b>{i}.</b> {match['team_home']} — {match['team_away']}\n"
        text += f"   📅 {time_str}{status_text}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="sport:football_champ")]
    ])

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


def get_back_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="sport:all")]
    ])
    return keyboard
