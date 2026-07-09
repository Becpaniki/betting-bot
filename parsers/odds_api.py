"""
Parser for The Odds API - free API for sports betting odds
Free tier: 500 requests/month
Register: https://the-odds-api.com/
"""
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime

from config import config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.the-odds-api.com/v4"


class OddsAPIParser:
    """Parser for The Odds API"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.ODDS_API_KEY
        self.base_url = BASE_URL

    async def get_sports(self) -> List[Dict]:
        """Get available sports"""
        url = f"{self.base_url}/sports"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params={"apiKey": self.api_key})
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error fetching sports: {e}")
                return []

    async def get_odds(self, sport: str, regions: str = "eu,uk", markets: str = "h2h") -> List[Dict]:
        """Get odds for a sport"""
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                logger.info(f"Fetched odds for {sport}: {len(response.json())} events, "
                           f"remaining requests: {response.headers.get('x-requests-remaining', '?')}")
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error for {sport}: {e.response.status_code} - {e.response.text}")
                return []
            except Exception as e:
                logger.error(f"Error fetching odds for {sport}: {e}")
                return []

    def parse_odds_response(self, events: List[Dict]) -> List[Dict]:
        """Parse API response into our format"""
        matches = []

        for event in events:
            try:
                match = {
                    "external_id": event.get("id", ""),
                    "sport": self._detect_sport(event.get("sport_key", "")),
                    "league": event.get("sport_title", ""),
                    "team_home": event.get("home_team", ""),
                    "team_away": event.get("away_team", ""),
                    "start_time": event.get("commence_time", ""),
                    "bookmakers": []
                }

                for bookmaker in event.get("bookmakers", []):
                    bm_name = bookmaker.get("title", "")

                    for market in bookmaker.get("markets", []):
                        if market.get("key") == "h2h":
                            outcomes = market.get("outcomes", [])
                            odds_data = {
                                "bookmaker": bm_name,
                                "outcome_home": None,
                                "outcome_draw": None,
                                "outcome_away": None
                            }

                            for outcome in outcomes:
                                name = outcome.get("name", "")
                                price = outcome.get("price", 0)

                                if name == event.get("home_team"):
                                    odds_data["outcome_home"] = price
                                elif name == event.get("away_team"):
                                    odds_data["outcome_away"] = price
                                elif name == "Draw":
                                    odds_data["outcome_draw"] = price

                            match["bookmakers"].append(odds_data)

                matches.append(match)

            except Exception as e:
                logger.error(f"Error parsing event: {e}")
                continue

        return matches

    def _detect_sport(self, sport_key: str) -> str:
        """Detect sport from API key"""
        if "soccer" in sport_key:
            return "football"
        elif "basketball" in sport_key:
            return "basketball"
        elif "icehockey" in sport_key or "hockey" in sport_key:
            return "hockey"
        elif "tennis" in sport_key:
            return "tennis"
        elif "baseball" in sport_key:
            return "baseball"
        elif "cricket" in sport_key:
            return "cricket"
        elif "mma" in sport_key or "boxing" in sport_key:
            return "martial"
        elif "americanfootball" in sport_key:
            return "american_football"
        return "other"


# Sport keys for The Odds API (top leagues only, to stay within 500 req/month)
SPORT_KEYS = {
    "football": [
        "soccer_epl",
        "soccer_spain_la_liga",
        "soccer_italy_serie_a",
    ],
    "basketball": [
        "basketball_nba_summer_league",
    ],
    "tennis": [
        "tennis_atp_wimbledon",
    ],
    "baseball": [
        "baseball_mlb",
    ],
    "martial": [
        "mma_mixed_martial_arts",
    ],
}

# Singleton
odds_api_parser = OddsAPIParser()
