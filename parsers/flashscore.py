"""
Parser for Flashscore.com - live results, schedules, statistics
Uses internal Flashscore API for data retrieval
"""
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_URL = "https://d.flashscore.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.flashscore.ru/",
    "Origin": "https://www.flashscore.ru",
}

# Sport IDs in Flashscore
SPORT_IDS = {
    "football": "1",
    "basketball": "2",
    "tennis": "3",
    "hockey": "4",
    "baseball": "5",
}


class FlashscoreParser:
    """Parser for Flashscore.com"""

    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.client = None

    async def _get_client(self):
        if self.client is None:
            self.client = httpx.AsyncClient(
                headers=self.headers,
                timeout=15.0,
                follow_redirects=True
            )
        return self.client

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def get_matches_by_sport(self, sport: str, limit: int = 10) -> List[Dict]:
        """Get popular matches for a sport"""
        sport_id = SPORT_IDS.get(sport)
        if not sport_id:
            return []

        url = f"{self.base_url}/x/feed/d_cr_1_{sport_id}_ru_1"
        client = await self._get_client()

        try:
            response = await client.get(url)
            if response.status_code == 200:
                return self._parse_matches_response(response.text, sport, limit)
            else:
                logger.warning(f"Flashscore returned {response.status_code} for {sport}")
                return []
        except Exception as e:
            logger.error(f"Error fetching Flashscore matches for {sport}: {e}")
            return []

    async def get_match_detail(self, match_id: str) -> Optional[Dict]:
        """Get detailed match information"""
        url = f"{self.base_url}/x/feed/d_hh_{match_id}_ru_1"
        client = await self._get_client()

        try:
            response = await client.get(url)
            if response.status_code == 200:
                return self._parse_match_detail(response.text)
            return None
        except Exception as e:
            logger.error(f"Error fetching match detail: {e}")
            return None

    async def get_team_form(self, sport: str, team_name: str) -> Optional[Dict]:
        """Get team's recent form (last 5 matches)"""
        matches = await self.get_matches_by_sport(sport, limit=30)

        for match in matches:
            if (match.get("team_home", "").lower() == team_name.lower() or
                match.get("team_away", "").lower() == team_name.lower()):
                return {
                    "team": team_name,
                    "recent_results": match.get("team_home_form" if match.get("team_home", "").lower() == team_name.lower() else "team_away_form", ""),
                    "last_matches": []
                }

        return None

    def _parse_matches_response(self, text: str, sport: str, limit: int) -> List[Dict]:
        """Parse Flashscore feed response"""
        matches = []

        try:
            # Flashscore uses a custom format with ~ separator
            sections = text.split("~")

            current_match = {}
            for section in sections:
                if section.startswith("AE"):
                    # Match ID
                    if current_match.get("id"):
                        matches.append(current_match)
                        if len(matches) >= limit:
                            break
                    current_match = {"id": section[2:], "sport": sport}
                elif section.startswith("AB"):
                    # Match time
                    current_match["time"] = section[2:]
                elif section.startswith("AD"):
                    # Home team
                    current_match["team_home"] = section[2:]
                elif section.startswith("AF"):
                    # Away team
                    current_match["team_away"] = section[2:]
                elif section.startswith("AG"):
                    # Home score
                    current_match["score_home"] = section[2:]
                elif section.startswith("AH"):
                    # Away score
                    current_match["score_away"] = section[2:]
                elif section.startswith("AK"):
                    # League/tournament
                    current_match["league"] = section[2:]
                elif section.startswith("AA"):
                    # Match status (e.g., "1 Half", "Finished")
                    current_match["status"] = section[2:]

            # Don't forget the last match
            if current_match.get("id") and len(matches) < limit:
                matches.append(current_match)

        except Exception as e:
            logger.error(f"Error parsing Flashscore response: {e}")

        return matches

    def _parse_match_detail(self, text: str) -> Dict:
        """Parse detailed match information"""
        detail = {}

        try:
            sections = text.split("~")

            for section in sections:
                if section.startswith("AB"):
                    detail["time"] = section[2:]
                elif section.startswith("AD"):
                    detail["team_home"] = section[2:]
                elif section.startswith("AF"):
                    detail["team_away"] = section[2:]
                elif section.startswith("AG"):
                    detail["score_home"] = section[2:]
                elif section.startswith("AH"):
                    detail["score_away"] = section[2:]
                elif section.startswith("AK"):
                    detail["league"] = section[2:]
                elif section.startswith("AA"):
                    detail["status"] = section[2:]
                elif section.startswith("ZA"):
                    detail["stadium"] = section[2:]
                elif section.startswith("ZE"):
                    detail["referee"] = section[2:]

        except Exception as e:
            logger.error(f"Error parsing match detail: {e}")

        return detail


# Singleton
flashscore_parser = FlashscoreParser()
