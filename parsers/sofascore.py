import json
from typing import List, Dict, Optional
import logging
import httpx

from parsers import BaseParser
from config import config

logger = logging.getLogger(__name__)


class SofaScoreParser(BaseParser):
    """Парсер коэффициентов с SofaScore (API)"""

    def __init__(self):
        super().__init__()
        self.source_name = "sofascore"
        self.api_base = "https://api.sofascore.com/api"
        self.headers.update({
            "Accept": "application/json",
        })

    async def fetch_api(self, endpoint: str) -> Optional[Dict]:
        """Получить данные из API"""
        url = f"{self.api_base}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error fetching API {url}: {e}")
                return None
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}")
                return None

    async def parse_matches(self) -> List[Dict]:
        """Парсинг списка матчей из API"""
        # Получаем события на сегодня
        data = await self.fetch_api("/sport/football/scheduled-events/2024-01-15")

        if not data or "events" not in data:
            return []

        matches = []
        for event in data["events"]:
            try:
                match_info = {
                    "external_id": str(event.get("id", "")),
                    "sport": "football",
                    "league": event.get("tournament", {}).get("name", ""),
                    "team_home": event.get("homeTeam", {}).get("name", ""),
                    "team_away": event.get("awayTeam", {}).get("name", ""),
                    "start_time": event.get("startTimestamp"),
                    "url": f"https://www.sofascore.com/event/{event.get('id', '')}",
                }
                matches.append(match_info)
            except Exception as e:
                logger.warning(f"Error parsing event: {e}")

        return matches

    async def parse_odds(self, match_url: str) -> List[Dict]:
        """Парсинг коэффициентов для матча"""
        # Извлекаем ID матча из URL
        import re
        match_id_match = re.search(r'/event/(\d+)', match_url)
        if not match_id_match:
            return []

        match_id = match_id_match.group(1)

        # Получаем коэффициенты из API
        data = await self.fetch_api(f"/event/{match_id}/odds/1/all")

        if not data or "markets" not in data:
            return []

        odds_list = []

        # Ищем рынок 1x2 (победа хозяев/ничья/победа гостей)
        for market in data.get("markets", []):
            if market.get("marketName") == "Match result" or market.get("marketName") == "1X2":
                # SofaScore не показывает отдельных букмекеров в публичном API
                # Обычно это агрегированные коэффициенты
                choices = market.get("choices", [])
                if len(choices) >= 3:
                    try:
                        odds_list.append({
                            "bookmaker": "SofaScore (aggregated)",
                            "outcome_home": float(choices[0].get("winRunnerOdds", {}).get("decimalValue", 0)),
                            "outcome_draw": float(choices[1].get("winRunnerOdds", {}).get("decimalValue", 0)),
                            "outcome_away": float(choices[2].get("winRunnerOdds", {}).get("decimalValue", 0)),
                        })
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error parsing odds: {e}")

        return odds_list

    async def get_team_statistics(self, team_id: int) -> Optional[Dict]:
        """Получить статистику команды"""
        return await self.fetch_api(f"/team/{team_id}/standings/total")

    async def get_match_statistics(self, match_id: int) -> Optional[Dict]:
        """Получить статистику матча"""
        return await self.fetch_api(f"/event/{match_id}/statistics")
