"""
Match statistics and form parser
Uses public APIs and calculates form statistics
"""
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


class StatsParser:
    """Parser for match statistics and team form"""

    def __init__(self):
        self.headers = HEADERS

    async def get_team_form(self, team_id: int) -> Optional[Dict]:
        """Get team recent form from SofaScore"""
        url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0"

        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    events = data.get("events", [])[:10]  # Last 10 matches
                    return self._calculate_form(events)
                return None
            except Exception as e:
                logger.error(f"Error fetching team form: {e}")
                return None

    async def search_team(self, team_name: str) -> Optional[int]:
        """Search for team ID by name"""
        url = f"https://api.sofascore.com/api/v1/search/teams/{team_name}"

        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    teams = data.get("results", [])
                    if teams:
                        return teams[0].get("entity", {}).get("id")
                return None
            except Exception as e:
                logger.error(f"Error searching team: {e}")
                return None

    def _calculate_form(self, events: List[Dict]) -> Dict:
        """Calculate team form from recent events"""
        if not events:
            return {"wins": 0, "draws": 0, "losses": 0, "form": ""}

        wins = 0
        draws = 0
        losses = 0
        form = []

        for event in events:
            home = event.get("homeTeam", {})
            away = event.get("awayTeam", {})
            result = event.get("result", {})

            home_score = result.get("homeScore", 0)
            away_score = result.get("awayScore", 0)

            if home_score > away_score:
                form.append("W")
                wins += 1
            elif home_score < away_score:
                form.append("L")
                losses += 1
            else:
                form.append("D")
                draws += 1

        return {
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "form": "".join(form[:5]),  # Last 5 matches
            "matches_played": len(events)
        }

    def calculate_prediction(self, home_form: Dict, away_form: Dict, home_odds: float, away_odds: float) -> Dict:
        """Calculate prediction based on form and odds"""
        # Base probabilities from odds
        if home_odds > 0:
            home_prob = 1 / home_odds
        else:
            home_prob = 0.33

        if away_odds > 0:
            away_prob = 1 / away_odds
        else:
            away_prob = 0.33

        draw_prob = 1 - home_prob - away_prob
        if draw_prob < 0:
            draw_prob = 0.25

        # Adjust based on form
        home_wins = home_form.get("wins", 0)
        away_wins = away_form.get("wins", 0)
        home_losses = home_form.get("losses", 0)
        away_losses = away_form.get("losses", 0)

        # Simple form adjustment
        if home_wins > away_wins:
            home_prob *= 1.1
        elif away_wins > home_wins:
            away_prob *= 1.1

        if home_losses > away_losses:
            away_prob *= 1.05
        elif away_losses > home_losses:
            home_prob *= 1.05

        # Normalize
        total = home_prob + draw_prob + away_prob
        home_prob = home_prob / total * 100
        draw_prob = draw_prob / total * 100
        away_prob = away_prob / total * 100

        return {
            "home": round(home_prob, 1),
            "draw": round(draw_prob, 1),
            "away": round(away_prob, 1),
            "home_form": home_form.get("form", ""),
            "away_form": away_form.get("form", ""),
            "confidence": round(max(home_prob, away_prob), 1)
        }


# Singleton
stats_parser = StatsParser()
