"""
Script to initialize the database and optionally add test data
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, SessionLocal
from database.models import User, Match, Odds
from database.crud import get_or_create_match, create_odds


def init_database():
    """Initialize the database"""
    print("Initializing database...")
    init_db()
    print("✅ Database initialized")


def add_test_data():
    """Add some test data for demonstration"""
    print("Adding test data...")

    db = SessionLocal()
    try:
        # Create test matches
        test_matches = [
            {
                "external_id": "test_1",
                "sport": "football",
                "league": "Премьер-лига",
                "team_home": "Спартак",
                "team_away": "ЦСКА",
                "start_time": datetime.now() + timedelta(hours=2),
            },
            {
                "external_id": "test_2",
                "sport": "football",
                "league": "Премьер-лига",
                "team_home": "Зенит",
                "team_away": "Локомотив",
                "start_time": datetime.now() + timedelta(hours=4),
            },
            {
                "external_id": "test_3",
                "sport": "basketball",
                "league": "Евролига",
                "team_home": "ЦСКА",
                "team_away": "Маккаби",
                "start_time": datetime.now() + timedelta(hours=6),
            },
        ]

        for match_data in test_matches:
            match = get_or_create_match(db, **match_data)

            # Add odds from different bookmakers
            test_odds = [
                {
                    "bookmaker": "1xBet",
                    "outcome_home": 2.15,
                    "outcome_draw": 3.40,
                    "outcome_away": 3.20,
                },
                {
                    "bookmaker": "Лига Ставок",
                    "outcome_home": 2.10,
                    "outcome_draw": 3.35,
                    "outcome_away": 3.25,
                },
                {
                    "bookmaker": "Фонбет",
                    "outcome_home": 2.05,
                    "outcome_draw": 3.30,
                    "outcome_away": 3.30,
                },
                {
                    "bookmaker": "Bet365",
                    "outcome_home": 2.20,
                    "outcome_draw": 3.45,
                    "outcome_away": 3.15,
                },
            ]

            for odds_data in test_odds:
                create_odds(db, match.id, **odds_data)

        print("✅ Test data added")

    finally:
        db.close()


if __name__ == "__main__":
    init_database()

    # Ask if user wants to add test data
    response = input("Add test data? (y/n): ").strip().lower()
    if response == "y":
        add_test_data()

    print("\nDone! You can now run the bot with: python main.py")
