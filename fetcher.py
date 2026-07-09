"""
Fetch real odds from The Odds API and save to database
"""
import asyncio
import logging
from datetime import datetime, timezone

from parsers.odds_api import odds_api_parser, SPORT_KEYS
from database import SessionLocal
from database.crud import get_or_create_match, create_odds
from database.models import Match, Odds

logger = logging.getLogger(__name__)


async def fetch_and_save_odds():
    """Fetch odds from API and save to database"""
    db = SessionLocal()
    total_matches = 0
    total_odds = 0

    try:
        for sport, sport_keys in SPORT_KEYS.items():
            for sport_key in sport_keys:
                try:
                    events = await odds_api_parser.get_odds(sport_key)
                    if not events:
                        continue

                    parsed = odds_api_parser.parse_odds_response(events)

                    for match_data in parsed:
                        # Parse start time
                        start_time = None
                        if match_data.get("start_time"):
                            try:
                                start_time = datetime.fromisoformat(
                                    match_data["start_time"].replace("Z", "+00:00")
                                )
                            except (ValueError, TypeError):
                                pass

                        # Create or get match
                        match = get_or_create_match(
                            db,
                            external_id=match_data["external_id"],
                            sport=match_data["sport"],
                            team_home=match_data["team_home"],
                            team_away=match_data["team_away"],
                            league=match_data["league"],
                            start_time=start_time
                        )

                        # Save odds for each bookmaker
                        for bm_odds in match_data.get("bookmakers", []):
                            bookmaker = bm_odds.get("bookmaker", "")
                            if not bookmaker:
                                continue

                            # Check if odds already exist for this match+bookmaker+time
                            existing = db.query(Odds).filter(
                                Odds.match_id == match.id,
                                Odds.bookmaker == bookmaker,
                                Odds.parsed_at > datetime.now(timezone.utc).replace(
                                    hour=datetime.now(timezone.utc).hour - 1
                                ) if datetime.now(timezone.utc).hour > 0 else datetime.now(timezone.utc)
                            ).first()

                            if not existing:
                                create_odds(
                                    db,
                                    match_id=match.id,
                                    bookmaker=bookmaker,
                                    market_type="1x2",
                                    outcome_home=bm_odds.get("outcome_home"),
                                    outcome_draw=bm_odds.get("outcome_draw"),
                                    outcome_away=bm_odds.get("outcome_away")
                                )
                                total_odds += 1

                        total_matches += 1

                    logger.info(f"Fetched {sport_key}: {len(parsed)} matches")

                except Exception as e:
                    logger.error(f"Error processing {sport_key}: {e}")
                    continue

                # Small delay between requests
                await asyncio.sleep(1)

        logger.info(f"Fetch complete: {total_matches} matches, {total_odds} new odds records")
        return total_matches, total_odds

    finally:
        db.close()


async def main():
    """Run fetcher standalone"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    matches, odds = await fetch_and_save_odds()
    print(f"\nDone! {matches} matches, {odds} odds records saved.")


if __name__ == "__main__":
    asyncio.run(main())
