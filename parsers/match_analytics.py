"""
Match analytics and predictions parser
Uses free APIs and odds analysis
"""
import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MatchAnalytics:
    """Analytics and predictions for matches"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def analyze_odds(self, odds_list: List[Dict]) -> Dict:
        """Analyze odds and calculate statistics"""
        if not odds_list:
            return {}

        analysis = {
            "best_odds": {},
            "margin": 0,
            "value_bets": [],
            "predictions": {},
            "confidence": 0
        }

        # Find best odds
        home_odds = [o.get("outcome_home", 0) for o in odds_list if o.get("outcome_home")]
        draw_odds = [o.get("outcome_draw", 0) for o in odds_list if o.get("outcome_draw")]
        away_odds = [o.get("outcome_away", 0) for o in odds_list if o.get("outcome_away")]

        if home_odds:
            best_home = max(odds_list, key=lambda x: x.get("outcome_home", 0))
            analysis["best_odds"]["home"] = {
                "odds": best_home.get("outcome_home"),
                "bookmaker": best_home.get("bookmaker", "")
            }

        if draw_odds:
            best_draw = max(odds_list, key=lambda x: x.get("outcome_draw", 0))
            analysis["best_odds"]["draw"] = {
                "odds": best_draw.get("outcome_draw"),
                "bookmaker": best_draw.get("bookmaker", "")
            }

        if away_odds:
            best_away = max(odds_list, key=lambda x: x.get("outcome_away", 0))
            analysis["best_odds"]["away"] = {
                "odds": best_away.get("outcome_away"),
                "bookmaker": best_away.get("bookmaker", "")
            }

        # Calculate implied probabilities
        if home_odds and draw_odds and away_odds:
            avg_home = sum(home_odds) / len(home_odds)
            avg_draw = sum(draw_odds) / len(draw_odds)
            avg_away = sum(away_odds) / len(away_odds)

            prob_home = 1 / avg_home
            prob_draw = 1 / avg_draw
            prob_away = 1 / avg_away

            total_prob = prob_home + prob_draw + prob_away
            analysis["margin"] = (total_prob - 1) * 100

            # Normalize probabilities
            analysis["predictions"] = {
                "home": round(prob_home / total_prob * 100, 1),
                "draw": round(prob_draw / total_prob * 100, 1),
                "away": round(prob_away / total_prob * 100, 1)
            }

            # Determine favorite
            if prob_home > prob_away:
                analysis["favorite"] = "home"
                analysis["confidence"] = round(prob_home / total_prob * 100, 1)
            else:
                analysis["favorite"] = "away"
                analysis["confidence"] = round(prob_away / total_prob * 100, 1)

            # Find value bets
            for odds_data in odds_list:
                bm = odds_data.get("bookmaker", "")

                if odds_data.get("outcome_home"):
                    value = (prob_home / odds_data["outcome_home"]) - 1
                    if value > 0.03:
                        analysis["value_bets"].append({
                            "bookmaker": bm,
                            "outcome": "П1",
                            "odds": odds_data["outcome_home"],
                            "value": round(value * 100, 1)
                        })

                if odds_data.get("outcome_away"):
                    value = (prob_away / odds_data["outcome_away"]) - 1
                    if value > 0.03:
                        analysis["value_bets"].append({
                            "bookmaker": bm,
                            "outcome": "П2",
                            "odds": odds_data["outcome_away"],
                            "value": round(value * 100, 1)
                        })

        return analysis

    def format_analytics(self, match: Dict, analysis: Dict, odds_list: List[Dict]) -> str:
        """Format analytics into readable text"""
        text = ""

        # Match info
        sport_emoji = {"football": "⚽", "basketball": "🏀", "hockey": "🏒", "tennis": "🎾"}.get(match.get("sport"), "🏟")
        text += f"{sport_emoji} <b>{match.get('team_home', '?')} vs {match.get('team_away', '?')}</b>\n"
        text += f"📅 {match.get('start_time', 'TBD')}\n"
        text += f"🏆 {match.get('league', '')}\n\n"

        # Predictions
        if analysis.get("predictions"):
            preds = analysis["predictions"]
            text += "📊 <b>Прогноз (на основе коэффициентов):</b>\n"
            text += f"🏠 {match.get('team_home', '?')}: <b>{preds['home']}%</b>\n"
            text += f"🤝 Ничья: <b>{preds['draw']}%</b>\n"
            text += f"✈️ {match.get('team_away', '?')}: <b>{preds['away']}%</b>\n\n"

            # Favorite
            if analysis.get("favorite") == "home":
                fav = match.get("team_home", "?")
            else:
                fav = match.get("team_away", "?")
            text += f"⭐ <b>Фаворит:</b> {fav} (уверенность {analysis['confidence']}%)\n\n"

        # Margin
        if analysis.get("margin"):
            margin = analysis["margin"]
            margin_emoji = "🟢" if margin < 5 else "🟡" if margin < 10 else "🔴"
            text += f"{margin_emoji} <b>Маржа букмекеров:</b> {margin:.1f}%\n\n"

        # Best odds
        if analysis.get("best_odds"):
            text += "🏆 <b>Лучшие коэффициенты:</b>\n"
            best = analysis["best_odds"]
            if "home" in best:
                text += f"🏠 П1: <b>{best['home']['odds']}</b> ({best['home']['bookmaker']})\n"
            if "draw" in best:
                text += f"🤝 X: <b>{best['draw']['odds']}</b> ({best['draw']['bookmaker']})\n"
            if "away" in best:
                text += f"✈️ П2: <b>{best['away']['odds']}</b> ({best['away']['bookmaker']})\n"
            text += "\n"

        # Value bets
        if analysis.get("value_bets"):
            text += "💰 <b>Value-ставки (завышенные коэффициенты):</b>\n"
            for vb in analysis["value_bets"][:3]:
                text += f"  🔥 {vb['outcome']}: {vb['odds']} (+{vb['value']}%) в {vb['bookmaker']}\n"
            text += "\n"

        # All bookmakers
        if odds_list:
            text += "📊 <b>Все коэффициенты:</b>\n"
            for o in odds_list:
                bm = o.get("bookmaker", "?")
                h = o.get("outcome_home", "-")
                d = o.get("outcome_draw", "-")
                a = o.get("outcome_away", "-")
                text += f"🏦 {bm}: {h} | {d} | {a}\n"

        return text


# Singleton
match_analytics = MatchAnalytics()
