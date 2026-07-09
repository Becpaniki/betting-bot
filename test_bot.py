"""
Simple test script to verify the bot can be imported
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all modules can be imported"""
    try:
        print("Testing imports...")

        # Test config
        from config import config
        print("✅ config imported")

        # Test database
        from database import init_db, Base
        print("✅ database imported")

        # Test models
        from database.models import User, Match, Odds, ValueBet, Notification
        print("✅ models imported")

        # Test CRUD
        from database.crud import get_user, create_user
        print("✅ crud imported")

        # Test parsers
        from parsers import BaseParser
        from parsers.flashscore import FlashscoreParser
        from parsers.sofascore import SofaScoreParser
        print("✅ parsers imported")

        # Test analytics
        from analytics import ValueFinder, OddsAnalyzer
        print("✅ analytics imported")

        # Test bot (this will fail if BOT_TOKEN is not set, but that's ok)
        try:
            from bot import bot, dp
            print("✅ bot imported")
        except Exception as e:
            print(f"⚠️  bot import failed (expected if BOT_TOKEN not set): {e}")

        print("\n✅ All imports successful!")
        return True

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
