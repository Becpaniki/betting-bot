"""Add realistic test data with different odds for each match"""
from datetime import datetime, timedelta
from database import init_db, SessionLocal
from database.models import Match, Odds
import random

init_db()
db = SessionLocal()

# Clear old data
db.query(Odds).delete()
db.query(Match).delete()
db.commit()

# Realistic matches with different odds
matches_data = [
    {
        "sport": "football", "league": "Премьер-лига",
        "team_home": "Спартак", "team_away": "ЦСКА", "hours": 2,
        "odds": {"1xBet": (2.15, 3.40, 3.20), "Лига Ставок": (2.10, 3.35, 3.25), "Фонбет": (2.05, 3.30, 3.30), "Bet365": (2.20, 3.45, 3.15)}
    },
    {
        "sport": "football", "league": "Премьер-лига",
        "team_home": "Зенит", "team_away": "Локомотив", "hours": 4,
        "odds": {"1xBet": (1.85, 3.60, 4.00), "Лига Ставок": (1.80, 3.55, 4.10), "Фонбет": (1.90, 3.50, 3.90), "Bet365": (1.82, 3.65, 4.05)}
    },
    {
        "sport": "football", "league": "Премьер-лига",
        "team_home": "Динамо", "team_away": "Краснодар", "hours": 6,
        "odds": {"1xBet": (2.50, 3.20, 2.80), "Лига Ставок": (2.45, 3.15, 2.85), "Фонбет": (2.55, 3.25, 2.75), "Bet365": (2.48, 3.18, 2.82)}
    },
    {
        "sport": "football", "league": "Лига чемпионов",
        "team_home": "Реал Мадрид", "team_away": "Барселона", "hours": 10,
        "odds": {"1xBet": (2.30, 3.30, 3.00), "Лига Ставок": (2.25, 3.25, 3.05), "Фонбет": (2.35, 3.35, 2.95), "Bet365": (2.28, 3.28, 3.02)}
    },
    {
        "sport": "football", "league": "АПЛ",
        "team_home": "Манчестер Сити", "team_away": "Ливерпуль", "hours": 12,
        "odds": {"1xBet": (2.10, 3.50, 3.30), "Лига Ставок": (2.05, 3.45, 3.35), "Фонбет": (2.15, 3.55, 3.25), "Bet365": (2.08, 3.48, 3.32)}
    },
    {
        "sport": "basketball", "league": "Евролига",
        "team_home": "ЦСКА", "team_away": "Маккаби", "hours": 3,
        "odds": {"1xBet": (1.75, 0, 2.05), "Лига Ставок": (1.70, 0, 2.10), "Фонбет": (1.80, 0, 2.00), "Bet365": (1.72, 0, 2.08)}
    },
    {
        "sport": "basketball", "league": "NBA",
        "team_home": "Лейкерс", "team_away": "Голден Стейт", "hours": 8,
        "odds": {"1xBet": (1.95, 0, 1.85), "Лига Ставок": (1.90, 0, 1.90), "Фонбет": (2.00, 0, 1.80), "Bet365": (1.92, 0, 1.88)}
    },
    {
        "sport": "basketball", "league": "NBA",
        "team_home": "Бостон", "team_away": "Милуоки", "hours": 11,
        "odds": {"1xBet": (1.65, 0, 2.20), "Лига Ставок": (1.60, 0, 2.25), "Фонбет": (1.70, 0, 2.15), "Bet365": (1.62, 0, 2.22)}
    },
    {
        "sport": "hockey", "league": "КХЛ",
        "team_home": "СКА", "team_away": "Ак Барс", "hours": 5,
        "odds": {"1xBet": (1.90, 3.80, 3.50), "Лига Ставок": (1.85, 3.75, 3.55), "Фонбет": (1.95, 3.85, 3.45), "Bet365": (1.88, 3.78, 3.52)}
    },
    {
        "sport": "hockey", "league": "NHL",
        "team_home": "Питтсбург", "team_away": "Вашингтон", "hours": 9,
        "odds": {"1xBet": (2.20, 3.70, 2.90), "Лига Ставок": (2.15, 3.65, 2.95), "Фонбет": (2.25, 3.75, 2.85), "Bet365": (2.18, 3.68, 2.92)}
    },
    {
        "sport": "tennis", "league": "ATP Wimbledon",
        "team_home": "Джокович", "team_away": "Алькарас", "hours": 7,
        "odds": {"1xBet": (2.40, 0, 1.55), "Лига Ставок": (2.35, 0, 1.58), "Фонбет": (2.45, 0, 1.52), "Bet365": (2.38, 0, 1.56)}
    },
    {
        "sport": "tennis", "league": "ATP Wimbledon",
        "team_home": "Медведев", "team_away": "Зверев", "hours": 13,
        "odds": {"1xBet": (1.80, 0, 2.00), "Лига Ставок": (1.75, 0, 2.05), "Фонбет": (1.85, 0, 1.95), "Bet365": (1.78, 0, 2.02)}
    },
]

for match_data in matches_data:
    match = Match(
        external_id=f"test_{match_data['team_home']}_{match_data['team_away']}",
        sport=match_data["sport"],
        league=match_data["league"],
        team_home=match_data["team_home"],
        team_away=match_data["team_away"],
        start_time=datetime.now() + timedelta(hours=match_data["hours"])
    )
    db.add(match)
    db.flush()

    for bookmaker, (home, draw, away) in match_data["odds"].items():
        odds = Odds(
            match_id=match.id,
            bookmaker=bookmaker,
            market_type="1x2",
            outcome_home=home,
            outcome_draw=draw,
            outcome_away=away
        )
        db.add(odds)

db.commit()
print(f"✅ Added {len(matches_data)} matches with unique odds")
db.close()
