"""
Telegram bot for sports betting analysis
"""
import asyncio
import logging
from dotenv import load_dotenv
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///betting.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    notify_value_bets = Column(Boolean, default=True)
    min_value_threshold = Column(Float, default=0.05)


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    external_id = Column(String, index=True)
    sport = Column(String, index=True)
    league = Column(String, nullable=True)
    team_home = Column(String)
    team_away = Column(String)
    start_time = Column(DateTime, nullable=True)


class Odds(Base):
    __tablename__ = "odds"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, index=True)
    bookmaker = Column(String)
    market_type = Column(String, default="1x2")
    outcome_home = Column(Float)
    outcome_draw = Column(Float)
    outcome_away = Column(Float)


Base.metadata.create_all(bind=engine)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


SPORT_EMOJI = {"football": "⚽", "basketball": "🏀", "hockey": "🏒", "tennis": "🎾"}
SPORT_NAME = {"football": "Футбол", "basketball": "Баскетбол", "hockey": "Хоккей", "tennis": "Теннис"}


# ============ Analytics Functions ============

def calculate_prediction(odds_list):
    """Calculate prediction based on odds from multiple bookmakers"""
    if not odds_list:
        return None

    home_odds = [o.outcome_home for o in odds_list if o.outcome_home and o.outcome_home > 0]
    draw_odds = [o.outcome_draw for o in odds_list if o.outcome_draw and o.outcome_draw > 0]
    away_odds = [o.outcome_away for o in odds_list if o.outcome_away and o.outcome_away > 0]

    if not home_odds or not away_odds:
        return None

    # Average odds
    avg_home = sum(home_odds) / len(home_odds)
    avg_draw = sum(draw_odds) / len(draw_odds) if draw_odds else 3.5
    avg_away = sum(away_odds) / len(away_odds)

    # Convert to probabilities
    prob_home = 1 / avg_home
    prob_draw = 1 / avg_draw
    prob_away = 1 / avg_away

    total = prob_home + prob_draw + prob_away

    # Normalize
    prob_home = prob_home / total * 100
    prob_draw = prob_draw / total * 100
    prob_away = prob_away / total * 100

    # Margin
    margin = (total - 1) * 100

    # Favorite
    if prob_home > prob_away:
        favorite = "home"
        confidence = prob_home
    else:
        favorite = "away"
        confidence = prob_away

    return {
        "home": round(prob_home, 1),
        "draw": round(prob_draw, 1),
        "away": round(prob_away, 1),
        "margin": round(margin, 1),
        "favorite": favorite,
        "confidence": round(confidence, 1)
    }


def find_value_bets(odds_list):
    """Find value bets (overpriced odds)"""
    if len(odds_list) < 2:
        return []

    home_odds = [o.outcome_home for o in odds_list if o.outcome_home and o.outcome_home > 0]
    draw_odds = [o.outcome_draw for o in odds_list if o.outcome_draw and o.outcome_draw > 0]
    away_odds = [o.outcome_away for o in odds_list if o.outcome_away and o.outcome_away > 0]

    if not home_odds or not away_odds:
        return []

    # Fair odds (average)
    fair_home = sum(home_odds) / len(home_odds)
    fair_draw = sum(draw_odds) / len(draw_odds) if draw_odds else 3.5
    fair_away = sum(away_odds) / len(away_odds)

    value_bets = []

    for o in odds_list:
        # Check home
        if o.outcome_home and o.outcome_home > 0:
            value = (fair_home / o.outcome_home) - 1
            if value > 0.03:
                value_bets.append({
                    "outcome": "П1",
                    "odds": o.outcome_home,
                    "bookmaker": o.bookmaker,
                    "value": round(value * 100, 1)
                })

        # Check away
        if o.outcome_away and o.outcome_away > 0:
            value = (fair_away / o.outcome_away) - 1
            if value > 0.03:
                value_bets.append({
                    "outcome": "П2",
                    "odds": o.outcome_away,
                    "bookmaker": o.bookmaker,
                    "value": round(value * 100, 1)
                })

    return sorted(value_bets, key=lambda x: x["value"], reverse=True)[:3]


# ============ Keyboards ============

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚽ Футбол", callback_data="sport:football"),
            InlineKeyboardButton(text="🏀 Баскетбол", callback_data="sport:basketball"),
        ],
        [
            InlineKeyboardButton(text="🏒 Хоккей", callback_data="sport:hockey"),
            InlineKeyboardButton(text="🎾 Теннис", callback_data="sport:tennis"),
        ],
        [
            InlineKeyboardButton(text="💰 Value-ставки", callback_data="value:show"),
            InlineKeyboardButton(text="📊 Все матчи", callback_data="matches:all"),
        ],
    ])


def get_back():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main"),
        ]
    ])


def format_odds_short(odds_list):
    """Format odds from multiple bookmakers in compact form"""
    if not odds_list:
        return "   📊 Коэффициенты не загружены\n"

    best_home = max(odds_list, key=lambda x: x.outcome_home or 0)
    best_draw = max(odds_list, key=lambda x: x.outcome_draw or 0)
    best_away = max(odds_list, key=lambda x: x.outcome_away or 0)

    text = f"   🏠 <b>{best_home.outcome_home}</b> ({best_home.bookmaker})\n"
    text += f"   🤝 <b>{best_draw.outcome_draw}</b> ({best_draw.bookmaker})\n"
    text += f"   ✈️ <b>{best_away.outcome_away}</b> ({best_away.bookmaker})\n"
    return text


def format_analytics(match, odds_list):
    """Format full analytics for a match"""
    sport_emoji = SPORT_EMOJI.get(match.sport, "🏟")
    time_str = match.start_time.strftime('%d.%m %H:%M') if match.start_time else "TBD"

    text = f"{sport_emoji} <b>{match.team_home} vs {match.team_away}</b>\n"
    text += f"📅 {time_str} | 🏆 {match.league or ''}\n\n"

    if not odds_list:
        text += "📊 Коэффициенты пока не загружены"
        return text

    # Calculate prediction
    pred = calculate_prediction(odds_list)

    if pred:
        text += "📊 <b>Прогноз (на основе коэффициентов):</b>\n"
        text += f"🏠 {match.team_home}: <b>{pred['home']}%</b>\n"
        text += f"🤝 Ничья: <b>{pred['draw']}%</b>\n"
        text += f"✈️ {match.team_away}: <b>{pred['away']}%</b>\n\n"

        # Favorite
        if pred["favorite"] == "home":
            fav = match.team_home
            fav_pct = pred["home"]
        else:
            fav = match.team_away
            fav_pct = pred["away"]

        if fav_pct > 60:
            star = "⭐"
        elif fav_pct > 45:
            star = "📊"
        else:
            star = "🤝"

        text += f"{star} <b>Фаворит:</b> {fav} ({fav_pct}%)\n\n"

        # Margin
        margin = pred["margin"]
        if margin < 5:
            margin_emoji = "🟢"
        elif margin < 10:
            margin_emoji = "🟡"
        else:
            margin_emoji = "🔴"
        text += f"{margin_emoji} <b>Маржа:</b> {margin}%\n\n"

    # Best odds
    text += "🏆 <b>Лучшие коэффициенты:</b>\n"
    best_home = max(odds_list, key=lambda x: x.outcome_home or 0)
    best_draw = max(odds_list, key=lambda x: x.outcome_draw or 0)
    best_away = max(odds_list, key=lambda x: x.outcome_away or 0)

    text += f"🏠 П1: <b>{best_home.outcome_home}</b> ({best_home.bookmaker})\n"
    if best_draw.outcome_draw:
        text += f"🤝 X: <b>{best_draw.outcome_draw}</b> ({best_draw.bookmaker})\n"
    text += f"✈️ П2: <b>{best_away.outcome_away}</b> ({best_away.bookmaker})\n\n"

    # Value bets
    value_bets = find_value_bets(odds_list)
    if value_bets:
        text += "💰 <b>Value-ставки (завышенные):</b>\n"
        for vb in value_bets:
            text += f"  🔥 {vb['outcome']}: {vb['odds']} (+{vb['value']}%) в {vb['bookmaker']}\n"
        text += "\n"

    # All bookmakers
    text += "📊 <b>Все букмекеры:</b>\n"
    for o in odds_list:
        h = o.outcome_home or "-"
        d = o.outcome_draw or "-"
        a = o.outcome_away or "-"
        text += f"🏦 {o.bookmaker}: {h} | {d} | {a}\n"

    return text


# ============ Handlers ============

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    logger.info(f"=== START COMMAND RECEIVED from {message.from_user.id} ({message.from_user.first_name}) ===")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        if not user:
            user = User(telegram_id=message.from_user.id, username=message.from_user.username, first_name=message.from_user.first_name)
            db.add(user)
            db.commit()
            logger.info(f"Created new user: {message.from_user.id}")
        else:
            logger.info(f"Existing user found: {message.from_user.id}")
    finally:
        db.close()

    text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я помогу находить выгодные ставки на спорт.\n\n"
        "Выбери вид спорта или действие 👇"
    )
    logger.info(f"Sending welcome message to {message.from_user.id}")
    await message.answer(text, reply_markup=get_main_menu())
    logger.info(f"Message sent successfully")


@dp.callback_query(F.data == "menu:main")
async def callback_main(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери действие 👇", reply_markup=get_main_menu())
    await callback.answer()


@dp.callback_query(F.data.startswith("sport:"))
async def callback_sport(callback: types.CallbackQuery):
    sport = callback.data.split(":")[1]
    emoji = SPORT_EMOJI.get(sport, "🏟")
    name = SPORT_NAME.get(sport, sport)

    db = SessionLocal()
    try:
        matches = db.query(Match).filter(Match.sport == sport).order_by(Match.start_time).limit(8).all()

        if not matches:
            text = f"{emoji} <b>{name}</b>\n\n📭 Матчей пока нет"
            await callback.message.edit_text(text, reply_markup=get_back())
            await callback.answer()
            return

        text = f"{emoji} <b>{name}</b> — ближайшие матчи:\n\nВыбери матч 👇\n"

        # Create buttons for each match
        buttons = []
        for m in matches:
            time_str = m.start_time.strftime("%d.%m %H:%M") if m.start_time else "TBD"
            btn_text = f"⚽ {m.team_home} vs {m.team_away} ({time_str})"
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"match:{m.id}")])

        # Add back buttons
        buttons.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main"),
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    finally:
        db.close()

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "matches:all")
async def callback_all_matches(callback: types.CallbackQuery):
    db = SessionLocal()
    try:
        matches = db.query(Match).order_by(Match.start_time).limit(8).all()

        if not matches:
            text = "📭 Матчей пока нет"
            await callback.message.edit_text(text, reply_markup=get_back())
            await callback.answer()
            return

        text = "📋 <b>Все матчи:</b>\n\nВыбери матч 👇\n"

        # Create buttons for each match
        buttons = []
        for m in matches:
            time_str = m.start_time.strftime("%d.%m %H:%M") if m.start_time else "TBD"
            sport_emoji = SPORT_EMOJI.get(m.sport, "🏟")
            btn_text = f"{sport_emoji} {m.team_home} vs {m.team_away} ({time_str})"
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"match:{m.id}")])

        # Add back buttons
        buttons.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main"),
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    finally:
        db.close()

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data.startswith("match:"))
async def callback_match_odds(callback: types.CallbackQuery):
    match_id = int(callback.data.split(":")[1])

    db = SessionLocal()
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            await callback.answer("Матч не найден", show_alert=True)
            return

        odds_list = db.query(Odds).filter(Odds.match_id == match_id).all()
        text = format_analytics(match, odds_list)

    finally:
        db.close()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"match:{match_id}")],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main"),
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "value:show")
async def callback_value(callback: types.CallbackQuery):
    db = SessionLocal()
    try:
        matches = db.query(Match).all()
        value_bets = []

        for match in matches:
            odds_list = db.query(Odds).filter(Odds.match_id == match.id).all()
            if len(odds_list) < 2:
                continue

            home_odds = [o.outcome_home for o in odds_list if o.outcome_home and o.outcome_home > 0]
            draw_odds = [o.outcome_draw for o in odds_list if o.outcome_draw and o.outcome_draw > 0]
            away_odds = [o.outcome_away for o in odds_list if o.outcome_away and o.outcome_away > 0]

            if not home_odds or not away_odds:
                continue

            fair_home = sum(home_odds) / len(home_odds)
            fair_draw = sum(draw_odds) / len(draw_odds) if draw_odds else 3.5
            fair_away = sum(away_odds) / len(away_odds)

            for o in odds_list:
                if o.outcome_home and o.outcome_home > 0:
                    value = (fair_home / o.outcome_home) - 1
                    if value > 0.03:
                        value_bets.append({
                            "match": match, "bookmaker": o.bookmaker,
                            "outcome": f"П1 ({match.team_home})", "odds": o.outcome_home,
                            "fair": fair_home, "value": value * 100
                        })
                if o.outcome_away and o.outcome_away > 0:
                    value = (fair_away / o.outcome_away) - 1
                    if value > 0.03:
                        value_bets.append({
                            "match": match, "bookmaker": o.bookmaker,
                            "outcome": f"П2 ({match.team_away})", "odds": o.outcome_away,
                            "fair": fair_away, "value": value * 100
                        })

        value_bets.sort(key=lambda x: x["value"], reverse=True)

        if not value_bets:
            text = "💰 <b>Value-ставки</b>\n\nПока нет завышенных коэффициентов"
        else:
            text = "💰 <b>Value-ставки (завышенные коэффициенты):</b>\n\n"
            for vb in value_bets[:8]:
                level = "🔥" if vb["value"] > 10 else "⭐" if vb["value"] > 5 else "✅"
                text += f"{level} <b>{vb['value']:.1f}%</b>\n"
                text += f"⚽ {vb['match'].team_home} vs {vb['match'].team_away}\n"
                text += f"   🎯 {vb['outcome']}\n"
                text += f"   💵 {vb['odds']} (справедливый: {vb['fair']:.2f})\n"
                text += f"   🏦 {vb['bookmaker']}\n\n"
    finally:
        db.close()

    await callback.message.edit_text(text, reply_markup=get_back())
    await callback.answer()


async def main():
    logger.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
