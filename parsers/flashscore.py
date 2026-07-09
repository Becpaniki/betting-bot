import re
from typing import List, Dict, Optional
from datetime import datetime
import logging
from bs4 import BeautifulSoup

from parsers import BaseParser

logger = logging.getLogger(__name__)


class FlashscoreParser(BaseParser):
    """Парсер коэффициентов с Flashscore"""

    def __init__(self):
        super().__init__()
        self.source_name = "flashscore"
        self.base_url = "https://www.flashscore.com"
        self.odds_url = "https://www.flashscore.com/odds/"

    async def parse_matches(self) -> List[Dict]:
        """Парсинг списка матчей с коэффициентами"""
        html = await self.fetch(self.odds_url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        matches = []

        # Flashscore использует JavaScript для рендеринга,
        # поэтому базовый парсинг может не работать
        # В реальном проекте здесь нужен Playwright/Selenium

        # Заглушка для демонстрации
        logger.info("Flashscore requires JavaScript rendering. Use Playwright parser.")

        return matches

    async def parse_odds(self, match_url: str) -> List[Dict]:
        """Парсинг коэффициентов для конкретного матча"""
        html = await self.fetch(match_url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        odds_list = []

        # Ищем таблицу коэффициентов
        odds_table = soup.find('table', {'class': 'ui-table__body'})

        if odds_table:
            rows = odds_table.find_all('tr')
            for row in rows:
                bookmaker_cell = row.find('td', {'class': 'odds__bookmaker'})
                odds_cells = row.find_all('td', {'class': 'odds__odd'})

                if bookmaker_cell and len(odds_cells) >= 3:
                    bookmaker_name = bookmaker_cell.get_text(strip=True)
                    odds_values = [cell.get_text(strip=True) for cell in odds_cells[:3]]

                    try:
                        odds_list.append({
                            "bookmaker": bookmaker_name,
                            "outcome_home": float(odds_values[0]),
                            "outcome_draw": float(odds_values[1]),
                            "outcome_away": float(odds_values[2]),
                        })
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing odds: {e}")

        return odds_list

    def parse_match_info(self, match_element) -> Optional[Dict]:
        """Парсинг информации о матче из элемента"""
        try:
            # Команды
            home_team = match_element.find('span', {'class': 'event__participant--home'})
            away_team = match_element.find('span', {'class': 'event__participant--away'})

            # Время
            time_element = match_element.find('span', {'class': 'event__time'})

            if home_team and away_team:
                return {
                    "team_home": home_team.get_text(strip=True),
                    "team_away": away_team.get_text(strip=True),
                    "start_time": self.parse_time(time_element.get_text(strip=True)) if time_element else None,
                    "sport": "football",  # Flashscore главная страница обычно футбол
                }
        except Exception as e:
            logger.error(f"Error parsing match info: {e}")

        return None

    def parse_time(self, time_str: str) -> Optional[datetime]:
        """Парсинг времени"""
        try:
            # Формат: "14:30" или "Сегодня, 14:30"
            time_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
            if time_match:
                hour, minute = map(int, time_match.groups())
                now = datetime.now()
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except Exception as e:
            logger.error(f"Error parsing time: {e}")

        return None
