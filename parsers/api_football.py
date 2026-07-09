"""
Parser for API-Football (api-football.com)
Free tier: 100 requests/day
Register: https://www.api-football.com/
"""
import httpx
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://v3.football.api-sports.io"
API_KEY = ""  # Get free key at https://www.api-football.com/


class APIFootballParser:
    """Parser for API-Football"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or API_KEY
        self.base_url = BASE_URL

    async def get_predictions(self, league_id: int = None, season: int = 2024) -> List[Dict]:
        """Get match predictions"""
        url = f"{self.base_url}/predictions"
        params = {"season": season}
        if league_id:
            params["league"] = league_id

        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_predictions(data.get("response", []))
                else:
                    logger.warning(f"API returned {response.status_code}")
                    return []
            except Exception as e:
                logger.error(f"Error: {e}")
                return []

    def _parse_predictions(self, predictions: List[Dict]) -> List[Dict]:
        """Parse API predictions"""
        result = []

        for pred in predictions:
            try:
                match = pred.get("match", {})
                teams = pred.get("teams", {})
                predictions_data = pred.get("predictions", {})

                result.append({
                    "team_home": teams.get("home", {}).get("name", ""),
                    "team_away": teams.get("away", {}).get("name", ""),
                    "league": pred.get("league", {}).get("name", ""),
                    "country": pred.get("league", {}).get("country", ""),
                    "match_date": match.get("date", ""),
                    "prediction_home": predictions_data.get("home", 0),
                    "prediction_draw": predictions_data.get("draw", 0),
                    "prediction_away": predictions_data.get("away", 0),
                    "advice": predictions_data.get("advice", ""),
                    "win_or_lose": predictions_data.get("win_or_lose", ""),
                    "source": "API-Football"
                })
            except Exception as e:
                logger.error(f"Error parsing prediction: {e}")
                continue

        return result


# League IDs for reference
LEAGUES = {
    "premier_league": 39,
    "la_liga": 140,
    "bundesliga": 78,
    "serie_a": 135,
    "ligue_1": 61,
    "champions_league": 2,
    "europa_league": 3,
    "eredivisie": 88,
    "primeira_liga": 94,
    "championship": 40,
}
