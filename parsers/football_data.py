"""
Football data parser from football-data.org (free tier available)
"""
import httpx
import logging
from typing import List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Free API from football-data.org (10 requests/min)
BASE_URL = "https://api.football-data.org/v4"
API_KEY = ""  # Get free key at https://www.football-data.org/client/register


class FootballDataParser:
    """Parser for football-data.org API"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or API_KEY
        self.base_url = BASE_URL
        self.headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

    async def get_competitions(self) -> List[Dict]:
        """Get available competitions"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/competitions",
                    headers=self.headers
                )
                if response.status_code == 200:
                    return response.json().get("competitions", [])
            except Exception as e:
                logger.error(f"Error: {e}")
        return []

    async def get_matches(self, competition_code: str = None) -> List[Dict]:
        """Get upcoming matches"""
        url = f"{self.base_url}/matches"
        params = {"status": "SCHEDULED", "limit": 50}

        if competition_code:
            url = f"{self.base_url}/competitions/{competition_code}/matches"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("matches", data.get("resultSet", []))
                else:
                    logger.warning(f"API returned {response.status_code}")
            except Exception as e:
                logger.error(f"Error: {e}")
        return []


async def test():
    parser = FootballDataParser()
    matches = await parser.get_matches()
    print(f"Found {len(matches)} matches")
    for m in matches[:5]:
        home = m.get("homeTeam", {}).get("name", "?")
        away = m.get("awayTeam", {}).get("name", "?")
        print(f"  {home} vs {away}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
