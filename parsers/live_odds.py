"""
Live odds parser from public sources
"""
import httpx
import logging
import json
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


class LiveOddsParser:
    """Parser for live odds from various sources"""

    def __init__(self):
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(headers=HEADERS, timeout=30.0)
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def fetch_sofascore_odds(self) -> List[Dict]:
        """Fetch odds from SofaScore API"""
        try:
            # Get scheduled events
            response = await self.client.get(
                "https://api.sofascore.com/api/v1/sport/football/scheduled-events/2024-01-15"
            )
            if response.status_code != 200:
                logger.warning(f"SofaScore returned {response.status_code}")
                return []

            data = response.json()
            events = data.get("events", [])[:20]  # Limit to 20 events

            matches = []
            for event in events:
                try:
                    match = {
                        "external_id": str(event.get("id", "")),
                        "sport": "football",
                        "league": event.get("tournament", {}).get("name", ""),
                        "team_home": event.get("homeTeam", {}).get("name", ""),
                        "team_away": event.get("awayTeam", {}).get("name", ""),
                        "start_time": event.get("startTimestamp"),
                        "bookmakers": []
                    }

                    # Try to get odds
                    event_id = event.get("id")
                    if event_id:
                        odds_response = await self.client.get(
                            f"https://api.sofascore.com/api/v1/event/{event_id}/odds/1/all"
                        )
                        if odds_response.status_code == 200:
                            odds_data = odds_response.json()
                            markets = odds_data.get("markets", [])

                            for market in markets:
                                if market.get("marketName") in ["Match result", "1X2"]:
                                    choices = market.get("choices", [])
                                    if len(choices) >= 3:
                                        match["bookmakers"].append({
                                            "bookmaker": "SofaScore",
                                            "outcome_home": choices[0].get("winRunnerOdds", {}).get("decimalValue"),
                                            "outcome_draw": choices[1].get("winRunnerOdds", {}).get("decimalValue"),
                                            "outcome_away": choices[2].get("winRunnerOdds", {}).get("decimalValue"),
                                        })

                    if match["bookmakers"]:
                        matches.append(match)

                except Exception as e:
                    logger.error(f"Error parsing SofaScore event: {e}")
                    continue

            return matches

        except Exception as e:
            logger.error(f"Error fetching SofaScore odds: {e}")
            return []

    async def fetch_livescore_odds(self) -> List[Dict]:
        """Fetch odds from Livescore API"""
        try:
            response = await self.client.get(
                "https://www.livescore.com/api/v1/sport/football/sr:match:next/odds"
            )
            # This is a simplified example - real implementation may vary
            return []
        except Exception as e:
            logger.error(f"Error fetching Livescore odds: {e}")
            return []

    async def fetch_all_odds(self) -> List[Dict]:
        """Fetch odds from all available sources"""
        all_matches = []

        # Try SofaScore
        sofascore_matches = await self.fetch_sofascore_odds()
        all_matches.extend(sofascore_matches)
        logger.info(f"Fetched {len(sofascore_matches)} matches from SofaScore")

        return all_matches


# Sport mappings for The Odds API
SPORTS_MAPPING = {
    "football": [
        "soccer_epl",
        "soccer_spain_la_liga",
        "soccer_germany_bundesliga",
        "soccer_italy_serie_a",
        "soccer_france_ligue_one",
        "soccer_uefa_champs_league",
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


async def test_parser():
    """Test the parser"""
    async with LiveOddsParser() as parser:
        matches = await parser.fetch_all_odds()
        print(f"Found {len(matches)} matches")

        for match in matches[:5]:
            print(f"\n{match['team_home']} vs {match['team_away']}")
            for bookmaker in match.get("bookmakers", []):
                print(f"  {bookmaker['bookmaker']}: {bookmaker.get('outcome_home')} | {bookmaker.get('outcome_draw')} | {bookmaker.get('outcome_away')}")


if __name__ == "__main__":
    asyncio.run(test_parser())
