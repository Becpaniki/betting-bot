import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    # Telegram Bot Token (получить у @BotFather)
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # The Odds API (https://the-odds-api.com/)
    ODDS_API_KEY: str = os.getenv("ODDS_API_KEY", "")

    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///betting.db")

    # Настройки парсинга
    PARSE_INTERVAL_MINUTES: int = 180  # каждые 3 часа (экономия API: 500 req/month)
    REQUEST_DELAY_SECONDS: float = 3.0
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Источники данных
    SOURCES: List[str] = field(default_factory=lambda: [
        "flashscore",
        "sofascore",
    ])

    # Value betting пороги
    VALUE_THRESHOLD_GOOD: float = 0.05   # 5% - хорошая ставка
    VALUE_THRESHOLD_GREAT: float = 0.10  # 10% - отличная ставка
    VALUE_THRESHOLD_RARE: float = 0.15   # 15% - редкая возможность

    # Логирование
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
