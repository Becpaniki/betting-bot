"""
Parser for Championat.com - Russian sports data
Parses match schedules, results, and standings
"""
import httpx
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_URL = "https://www.championat.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Known tournament URLs on Championat.com
TOURNAMENS = {
    "worldcup": "/football/_worldcup/tournament/6858/calendar/",
    "rpl": "/football/_russiapl.html",
    "epl": "/football/_england.html",
    "laliga": "/football/_spain.html",
    "seriea": "/football/_italy.html",
    "bundesliga": "/football/_germany.html",
    "ligue1": "/football/_france.html",
    "champions": "/football/_ucl.html",
}


class ChampionatParser:
    """Parser for Championat.com"""

    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS

    async def get_calendar(self, tournament: str = "worldcup") -> List[Dict]:
        """Get match calendar from Championat"""
        path = TOURNAMENS.get(tournament)
        if not path:
            return []

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return self._parse_calendar(response.text)
                else:
                    logger.warning(f"Championat returned {response.status_code} for {tournament}")
                    return []
            except Exception as e:
                logger.error(f"Error fetching Championat calendar: {e}")
                return []

    async def get_match_review(self, url: str) -> Optional[Dict]:
        """Get match review/article"""
        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return self._parse_article(response.text)
                return None
            except Exception as e:
                logger.error(f"Error fetching match review: {e}")
                return None

    def _parse_calendar(self, html: str) -> List[Dict]:
        """Parse calendar page for match data"""
        matches = []

        try:
            # Look for match data in script tags (Championat uses JSON-LD or inline data)
            json_ld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
            json_ld_matches = re.findall(json_ld_pattern, html, re.DOTALL)

            for json_str in json_ld_matches:
                try:
                    import json
                    data = json.loads(json_str)
                    if isinstance(data, dict) and data.get("@type") == "SportsEvent":
                        match = {
                            "team_home": data.get("homeTeam", {}).get("name", ""),
                            "team_away": data.get("awayTeam", {}).get("name", ""),
                            "start_time": data.get("startDate", ""),
                            "league": data.get("location", {}).get("name", ""),
                            "status": data.get("eventStatus", ""),
                        }
                        if match["team_home"] and match["team_away"]:
                            matches.append(match)
                except json.JSONDecodeError:
                    continue

            # Also try to find match rows in HTML
            if not matches:
                # Look for common patterns in Championat HTML
                match_pattern = r'class="[^"]*match[^"]*"[^>]*>(.*?)</(?:div|tr)'
                match_rows = re.findall(match_pattern, html, re.DOTALL)

                for row in match_rows[:20]:
                    teams = re.findall(r'class="[^"]*team[^"]*"[^>]*>([^<]+)<', row)
                    if len(teams) >= 2:
                        matches.append({
                            "team_home": teams[0].strip(),
                            "team_away": teams[1].strip(),
                            "start_time": "",
                            "league": "",
                            "status": "",
                        })

        except Exception as e:
            logger.error(f"Error parsing Championat calendar: {e}")

        return matches

    def _parse_article(self, html: str) -> Dict:
        """Parse article page for content"""
        result = {}

        try:
            # Extract title
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
            if title_match:
                result["title"] = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()

            # Extract main image
            img_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
            if img_match:
                result["image"] = img_match.group(1)

            # Extract description
            desc_match = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
            if desc_match:
                result["description"] = desc_match.group(1)

        except Exception as e:
            logger.error(f"Error parsing Championat article: {e}")

        return result


# Singleton
championat_parser = ChampionatParser()
