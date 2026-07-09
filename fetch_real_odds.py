"""
Fetch real odds from The Odds API
FREE: 500 requests/month
Register: https://the-odds-api.com/
"""
import httpx
import asyncio
import json
from datetime import datetime, timedelta
from database import init_db, SessionLocal
from database.models import Match, Odds

# Get your FREE API key at: https://the-odds-api.com/#api-access
API_KEY = "9fe1dd13cfccb63c86a4921efc465024"

BASE_URL = "https://api.the-odds-api.com/v4"

SPORT_KEYS = {
    "football": [
        "soccer_epl",
        "soccer_spain_la_liga",
        "soccer_germany_bundesliga",
        "soccer_italy_serie_a",
        "soccer_france_ligue_one",
        "soccer_uefa_champs_league",
        "soccer_russia_premier_league",
    ],
    "basketball": [
        "basketball_nba",
        "basketball_euroleague",
    ],
    "hockey": [
        "icehockey_nhl",
    ],
    "tennis": [
        "tennis_atp",
    ],
}


async def fetch_odds(sport_key: str) -> list:
    """Fetch odds for a specific sport"""
    url = f"{BASE_URL}/sports/{sport_key}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu,uk",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"  Error {response.status_code}: {response.text[:100]}")
                return []
        except Exception as e:
            print(f"  Error: {e}")
            return []


def parse_events(events: list, sport: str) -> list:
    """Parse API events into our format"""
    matches = []

    for event in events:
        match = {
            "external_id": event.get("id", ""),
            "sport": sport,
            "league": event.get("sport_title", ""),
            "team_home": event.get("home_team", ""),
            "team_away": event.get("away_team", ""),
            "start_time": event.get("time_local", ""),
            "bookmakers": []
        }

        for bookmaker in event.get("bookmakers", []):
            bm_name = bookmaker.get("title", "")

            for market in bookmaker.get("markets", []):
                if market.get("key") == "h2h":
                    odds = {
                        "bookmaker": bm_name,
                        "outcome_home": None,
                        "outcome_draw": None,
                        "outcome_away": None
                    }

                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "")
                        price = outcome.get("price", 0)

                        if name == event.get("home_team"):
                            odds["outcome_home"] = price
                        elif name == event.get("away_team"):
                            odds["outcome_away"] = price
                        elif name == "Draw":
                            odds["outcome_draw"] = price

                    match["bookmakers"].append(odds)

        if match["bookmakers"]:
            matches.append(match)

    return matches


def save_to_database(matches: list):
    """Save matches to database"""
    init_db()
    db = SessionLocal()

    try:
        # Clear old data
        db.query(Odds).delete()
        db.query(Match).delete()
        db.commit()

        for match_data in matches:
            match = Match(
                external_id=match_data["external_id"],
                sport=match_data["sport"],
                league=match_data["league"],
                team_home=match_data["team_home"],
                team_away=match_data["team_away"],
                start_time=datetime.fromisoformat(match_data["start_time"].replace("Z", "+00:00")) if match_data["start_time"] else None
            )
            db.add(match)
            db.flush()

            for bookmaker in match_data["bookmakers"]:
                odds = Odds(
                    match_id=match.id,
                    bookmaker=bookmaker["bookmaker"],
                    outcome_home=bookmaker["outcome_home"],
                    outcome_draw=bookmaker["outcome_draw"],
                    outcome_away=bookmaker["outcome_away"]
                )
                db.add(odds)

        db.commit()
        print(f"\n✅ Saved {len(matches)} matches to database")

    finally:
        db.close()


async def main():
    if API_KEY == "YOUR_API_KEY_HERE":
        print("=" * 60)
        print("❌ НУЖЕН API КЛЮЧ!")
        print("=" * 60)
        print()
        print("1. Перейдите на: https://the-odds-api.com/#api-access")
        print("2. Зарегистрируйтесь (бесплатно)")
        print("3. Скопируйте API ключ")
        print("4. Вставьте его в файл fetch_real_odds.py (строка API_KEY)")
        print()
        print("Бесплатный тариф: 500 запросов в месяц")
        print("=" * 60)
        return

    print("Fetching real odds from The Odds API...")
    print()

    all_matches = []

    for sport, keys in SPORT_KEYS.items():
        print(f"📡 {sport.upper()}:")
        for key in keys:
            events = await fetch_odds(key)
            matches = parse_events(events, sport)
            all_matches.extend(matches)
            print(f"  {key}: {len(matches)} matches")
            await asyncio.sleep(0.5)  # Rate limit

    print(f"\n📊 Total: {len(all_matches)} matches")

    if all_matches:
        save_to_database(all_matches)

        # Show sample
        print("\n📋 Sample:")
        for m in all_matches[:5]:
            print(f"  {m['team_home']} vs {m['team_away']}")
            for b in m['bookmakers'][:2]:
                print(f"    {b['bookmaker']}: {b['outcome_home']} | {b['outcome_draw']} | {b['outcome_away']}")


if __name__ == "__main__":
    asyncio.run(main())
