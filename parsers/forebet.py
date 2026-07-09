"""
Parser for Forebet.com - real match predictions
"""
import httpx
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_URL = "https://forebet.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


class ForebetParser:
    """Parser for Forebet.com predictions"""

    def __init__(self):
        self.base_url = BASE_URL

    async def get_predictions(self, sport: str = "football") -> List[Dict]:
        """Get predictions from Forebet"""
        url = f"{self.base_url}/en/football-predictions"

        async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return self.parse_html(response.text)
                else:
                    logger.warning(f"Forebet returned {response.status_code}")
                    return []
            except Exception as e:
                logger.error(f"Error fetching Forebet: {e}")
                return []

    async def get_match_prediction(self, match_url: str) -> Optional[Dict]:
        """Get detailed prediction for a specific match"""
        async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
            try:
                response = await client.get(f"{self.base_url}{match_url}")
                if response.status_code == 200:
                    return self.parse_match_page(response.text)
                return None
            except Exception as e:
                logger.error(f"Error fetching match: {e}")
                return None

    def parse_html(self, html: str) -> List[Dict]:
        """Parse predictions from HTML"""
        predictions = []

        # Find prediction rows
        # Forebet uses specific CSS classes for prediction rows
        rows = re.findall(r'<tr[^>]*class="[^"]*pred[^"]*"[^>]*>(.*?)</tr>', html, re.DOTALL)

        for row in rows[:30]:  # Limit to 30 predictions
            try:
                pred = self._parse_row(row)
                if pred:
                    predictions.append(pred)
            except Exception as e:
                logger.error(f"Error parsing row: {e}")
                continue

        return predictions

    def _parse_row(self, row: str) -> Optional[Dict]:
        """Parse a single prediction row"""
        # Extract teams
        teams = re.findall(r'<a[^>]*>([^<]+)</a>', row)
        if len(teams) < 2:
            return None

        # Extract prediction percentages
        percents = re.findall(r'(\d+)%', row)
        if len(percents) < 3:
            return None

        # Extract odds if available
        odds = re.findall(r'<td[^>]*class="[^"]*odds[^"]*"[^>]*>([^<]+)</td>', row)

        # Extract match URL
        url_match = re.search(r'href="(/en/[^"]*\.htm)"', row)
        match_url = url_match.group(1) if url_match else None

        # Extract date
        date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', row)
        match_date = date_match.group(1) if date_match else None

        return {
            "team_home": teams[0].strip(),
            "team_away": teams[1].strip(),
            "prediction_home": int(percents[0]),
            "prediction_draw": int(percents[1]),
            "prediction_away": int(percents[2]),
            "odds_home": float(odds[0]) if odds and len(odds) > 0 else None,
            "odds_draw": float(odds[1]) if odds and len(odds) > 1 else None,
            "odds_away": float(odds[2]) if odds and len(odds) > 2 else None,
            "match_url": match_url,
            "date": match_date,
            "source": "Forebet"
        }

    def parse_match_page(self, html: str) -> Dict:
        """Parse detailed match prediction page"""
        result = {}

        # Extract prediction
        pred_match = re.search(r'(\d+)%\s*-\s*(\d+)%\s*-\s*(\d+)%', html)
        if pred_match:
            result["home"] = int(pred_match.group(1))
            result["draw"] = int(pred_match.group(2))
            result["away"] = int(pred_match.group(3))

        # Extract confidence
        conf_match = re.search(r'Confidence.*?(\d+)/10', html)
        if conf_match:
            result["confidence"] = int(conf_match.group(1))

        # Extract tips
        tips = re.findall(r'<span[^>]*class="[^"]*tip[^"]*"[^>]*>([^<]+)</span>', html)
        result["tips"] = tips[:3]

        return result


# Create instance
forebet_parser = ForebetParser()
