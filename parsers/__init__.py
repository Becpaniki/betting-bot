from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import httpx
import asyncio
import logging

from config import config

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Базовый класс для парсеров букмекеров"""

    def __init__(self):
        self.source_name = "base"
        self.headers = {
            "User-Agent": config.USER_AGENT,
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    async def fetch(self, url: str) -> Optional[str]:
        """Получить страницу"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.text
            except httpx.HTTPError as e:
                logger.error(f"Error fetching {url}: {e}")
                return None

    @abstractmethod
    async def parse_matches(self) -> List[Dict]:
        """Парсинг списка матчей"""
        pass

    @abstractmethod
    async def parse_odds(self, match_url: str) -> List[Dict]:
        """Парсинг коэффициентов для матча"""
        pass

    async def parse_all(self) -> List[Dict]:
        """Парсинг всех данных"""
        matches = await self.parse_matches()
        results = []

        for match in matches:
            odds = await self.parse_odds(match.get("url", ""))
            match["odds"] = odds
            results.append(match)

            # Задержка между запросами
            await asyncio.sleep(config.REQUEST_DELAY_SECONDS)

        return results

    def normalize_sport(self, sport_name: str) -> str:
        """Нормализация названия вида спорта"""
        sport_map = {
            "футбол": "football",
            "soccer": "football",
            "football": "football",
            "баскетбол": "basketball",
            "basketball": "basketball",
            "хоккей": "hockey",
            "hockey": "hockey",
            "ice hockey": "hockey",
            "теннис": "tennis",
            "tennis": "tennis",
            "киберспорт": "esports",
            "esports": "esports",
            "csgo": "esports",
            "cs2": "esports",
            "dota": "esports",
        }
        return sport_map.get(sport_name.lower(), sport_name.lower())
