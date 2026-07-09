from typing import List, Dict, Optional
import logging

from config import config

logger = logging.getLogger(__name__)


class ValueFinder:
    """Класс для поиска value-ставок"""

    def __init__(self):
        self.good_threshold = config.VALUE_THRESHOLD_GOOD
        self.great_threshold = config.VALUE_THRESHOLD_GREAT
        self.rare_threshold = config.VALUE_THRESHOLD_RARE

    def calculate_fair_odds(self, odds_list: List[float]) -> float:
        """
        Рассчитать справедливый коэффициент

        Справедливый коэффициент = 1 / (сумма обратных всех коэффициентов / кол-во коэффициентов)
        Это усреднённый коэффициент без маржи букмекера
        """
        if not odds_list:
            return 0.0

        # Преобразуем коэффициенты в вероятности
        implied_probabilities = [1 / odds for odds in odds_list if odds > 0]

        if not implied_probabilities:
            return 0.0

        # Суммируем вероятности
        total_prob = sum(implied_probabilities)

        # Справедливая вероятность (без маржи)
        fair_prob = 1 / total_prob

        # Справедливый коэффициент
        fair_odds = 1 / (fair_prob / len(odds_list))

        return fair_odds

    def calculate_value(self, odds_offered: float, fair_odds: float) -> float:
        """
        Рассчитать value ставки

        Value = (справедливый_коэф / предложенный_коэф) - 1
        Если Value > 0, ставка value
        """
        if odds_offered <= 0 or fair_odds <= 0:
            return 0.0

        value = (fair_odds / odds_offered) - 1
        return value

    def find_value_bets(self, matches: List[Dict]) -> List[Dict]:
        """
        Найти value-ставки среди матчей

        Args:
            matches: Список матчей с коэффициентами

        Returns:
            Список value-ставок
        """
        value_bets = []

        for match in matches:
            odds_list = match.get("odds", [])

            if len(odds_list) < 2:
                continue

            # Собираем коэффициенты по исходам
            home_odds = [o.get("outcome_home", 0) for o in odds_list if o.get("outcome_home", 0) > 0]
            draw_odds = [o.get("outcome_draw", 0) for o in odds_list if o.get("outcome_draw", 0) > 0]
            away_odds = [o.get("outcome_away", 0) for o in odds_list if o.get("outcome_away", 0) > 0]

            # Рассчитываем справедливые коэффициенты
            fair_home = self.calculate_fair_odds(home_odds)
            fair_draw = self.calculate_fair_odds(draw_odds)
            fair_away = self.calculate_fair_odds(away_odds)

            # Проверяем каждый коэффициент на value
            for odds_data in odds_list:
                bookmaker = odds_data.get("bookmaker", "Unknown")

                # Проверяем П1 (победа хозяев)
                if odds_data.get("outcome_home", 0) > 0:
                    value = self.calculate_value(odds_data["outcome_home"], fair_home)
                    if value > 0:
                        value_bets.append(self._create_value_bet(
                            match=match,
                            bookmaker=bookmaker,
                            outcome="home",
                            odds=odds_data["outcome_home"],
                            fair_odds=fair_home,
                            value=value,
                            probability=1 / fair_home
                        ))

                # Проверяем X (ничья)
                if odds_data.get("outcome_draw", 0) > 0:
                    value = self.calculate_value(odds_data["outcome_draw"], fair_draw)
                    if value > 0:
                        value_bets.append(self._create_value_bet(
                            match=match,
                            bookmaker=bookmaker,
                            outcome="draw",
                            odds=odds_data["outcome_draw"],
                            fair_odds=fair_draw,
                            value=value,
                            probability=1 / fair_draw
                        ))

                # Проверяем П2 (победа гостей)
                if odds_data.get("outcome_away", 0) > 0:
                    value = self.calculate_value(odds_data["outcome_away"], fair_away)
                    if value > 0:
                        value_bets.append(self._create_value_bet(
                            match=match,
                            bookmaker=bookmaker,
                            outcome="away",
                            odds=odds_data["outcome_away"],
                            fair_odds=fair_away,
                            value=value,
                            probability=1 / fair_away
                        ))

        # Сортируем по value (от наибольшего к наименьшему)
        value_bets.sort(key=lambda x: x["value"], reverse=True)

        return value_bets

    def _create_value_bet(self, match: Dict, bookmaker: str, outcome: str,
                          odds: float, fair_odds: float, value: float, probability: float) -> Dict:
        """Создать запись value-ставки"""
        # Определяем уровень value
        if value >= self.rare_threshold:
            level = "rare"
        elif value >= self.great_threshold:
            level = "great"
        elif value >= self.good_threshold:
            level = "good"
        else:
            level = "minor"

        return {
            "match": match,
            "bookmaker": bookmaker,
            "outcome": outcome,
            "odds": odds,
            "fair_odds": fair_odds,
            "value": value,
            "value_percentage": value * 100,
            "probability": probability,
            "level": level,
        }

    def get_value_label(self, value: float) -> str:
        """Получить текстовую метку для value"""
        if value >= self.rare_threshold:
            return "🔥 РЕДКАЯ"
        elif value >= self.great_threshold:
            return "⭐ ОТЛИЧНАЯ"
        elif value >= self.good_threshold:
            return "✅ ХОРОШАЯ"
        else:
            return "📊 ЕСТЬ"
