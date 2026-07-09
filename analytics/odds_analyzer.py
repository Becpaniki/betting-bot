from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class OddsAnalyzer:
    """Анализатор коэффициентов"""

    def __init__(self):
        pass

    def calculate_margin(self, odds_home: float, odds_draw: float, odds_away: float) -> float:
        """
        Рассчитать маржу букмекера

        Маржа = (сумма обратных коэффициентов) - 1
        Чем выше маржа, тем хуже коэффициенты для игрока
        """
        if odds_home <= 0 or odds_draw <= 0 or odds_away <= 0:
            return 0.0

        implied_probabilities = (1 / odds_home) + (1 / odds_draw) + (1 / odds_away)
        margin = implied_probabilities - 1

        return margin * 100  # В процентах

    def compare_odds(self, odds_list: List[Dict]) -> Dict:
        """
        Сравнить коэффициенты разных букмекеров

        Returns:
            Словарь с лучшими коэффициентами по каждому исходу
        """
        if not odds_list:
            return {}

        best_home = {"bookmaker": "", "odds": 0}
        best_draw = {"bookmaker": "", "odds": 0}
        best_away = {"bookmaker": "", "odds": 0}

        margins = []

        for odds_data in odds_list:
            bookmaker = odds_data.get("bookmaker", "Unknown")

            # Лучший коэффициент на П1
            if odds_data.get("outcome_home", 0) > best_home["odds"]:
                best_home = {"bookmaker": bookmaker, "odds": odds_data["outcome_home"]}

            # Лучший коэффициент на X
            if odds_data.get("outcome_draw", 0) > best_draw["odds"]:
                best_draw = {"bookmaker": bookmaker, "odds": odds_data["outcome_draw"]}

            # Лучший коэффициент на П2
            if odds_data.get("outcome_away", 0) > best_away["odds"]:
                best_away = {"bookmaker": bookmaker, "odds": odds_data["outcome_away"]}

            # Рассчитываем маржу
            margin = self.calculate_margin(
                odds_data.get("outcome_home", 0),
                odds_data.get("outcome_draw", 0),
                odds_data.get("outcome_away", 0)
            )
            margins.append({"bookmaker": bookmaker, "margin": margin})

        # Сортируем букмекеров по марже (от меньшей к большей)
        margins.sort(key=lambda x: x["margin"])

        return {
            "best_home": best_home,
            "best_draw": best_draw,
            "best_away": best_away,
            "margins": margins,
            "average_margin": sum(m["margin"] for m in margins) / len(margins) if margins else 0,
        }

    def format_comparison(self, odds_list: List[Dict], match_info: Dict = None) -> str:
        """Форматировать сравнение коэффициентов"""
        if not odds_list:
            return "Нет данных для сравнения"

        comparison = self.compare_odds(odds_list)

        text = ""
        if match_info:
            text += f"⚽ {match_info.get('team_home', '?')} vs {match_info.get('team_away', '?')}\n"
            text += "─" * 30 + "\n\n"

        text += "📊 **Лучшие коэффициенты:**\n"
        text += f"🏠 П1: {comparison['best_home']['odds']} ({comparison['best_home']['bookmaker']})\n"
        text += f"🤝 X: {comparison['best_draw']['odds']} ({comparison['best_draw']['bookmaker']})\n"
        text += f"✈️ П2: {comparison['best_away']['odds']} ({comparison['best_away']['bookmaker']})\n\n"

        text += f"📈 Средняя маржа: {comparison['average_margin']:.1f}%\n\n"

        if comparison['margins']:
            text += "🏦 **Маржа букмекеров:**\n"
            for m in comparison['margins'][:5]:
                emoji = "🟢" if m['margin'] < 5 else "🟡" if m['margin'] < 10 else "🔴"
                text += f"{emoji} {m['bookmaker']}: {m['margin']:.1f}%\n"

        return text

    def detect_odds_movement(self, historical_odds: List[Dict], current_odds: Dict) -> Optional[str]:
        """
        Обнаружить движение коэффициентов

        Returns:
            Описание изменения или None
        """
        if not historical_odds:
            return None

        prev_odds = historical_odds[-1]  # Берём последний известный коэффициент

        movements = []

        # Проверяем движение по каждому исходу
        for outcome in ["outcome_home", "outcome_draw", "outcome_away"]:
            prev_value = prev_odds.get(outcome, 0)
            curr_value = current_odds.get(outcome, 0)

            if prev_value > 0 and curr_value > 0:
                change = ((curr_value - prev_value) / prev_value) * 100

                if abs(change) > 1:  # Изменение более 1%
                    direction = "📈 вырос" if change > 0 else "📉 снизился"
                    outcome_name = {"outcome_home": "П1", "outcome_draw": "X", "outcome_away": "П2"}.get(outcome)
                    movements.append(f"{outcome_name} {direction} на {abs(change):.1f}%")

        if movements:
            return " | ".join(movements)

        return None
