from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """Пользователь Telegram"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Настройки уведомлений
    notify_value_bets = Column(Boolean, default=True)
    min_value_threshold = Column(Float, default=0.05)
    preferred_sports = Column(JSON, default=["football", "basketball", "hockey", "tennis"])

    # Связи
    notifications = relationship("Notification", back_populates="user")


class Match(Base):
    """Матч"""
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    external_id = Column(String, index=True)  # ID из источника
    sport = Column(String, index=True, nullable=False)  # football, basketball, etc.
    league = Column(String, nullable=True)
    team_home = Column(String, nullable=False)
    team_away = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=True)
    parsed_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    odds = relationship("Odds", back_populates="match")


class Odds(Base):
    """Коэффициенты букмекера"""
    __tablename__ = "odds"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    bookmaker = Column(String, index=True, nullable=False)
    market_type = Column(String, default="1x2")  # 1x2, totals, handicaps
    outcome_home = Column(Float, nullable=True)
    outcome_draw = Column(Float, nullable=True)
    outcome_away = Column(Float, nullable=True)
    parsed_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    match = relationship("Match", back_populates="odds")


class ValueBet(Base):
    """Value-ставка (рассчитанная)"""
    __tablename__ = "value_bets"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    bookmaker = Column(String, nullable=False)
    market_type = Column(String, default="1x2")
    outcome = Column(String, nullable=False)  # home, draw, away
    odds = Column(Float, nullable=False)
    fair_odds = Column(Float, nullable=False)
    value_percentage = Column(Float, nullable=False)  # e.g. 0.08 = 8%
    probability = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)

    # Связи
    match = relationship("Match")


class Notification(Base):
    """Отправленные уведомления"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    value_bet_id = Column(Integer, ForeignKey("value_bets.id"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)

    # Связи
    user = relationship("User", back_populates="notifications")
    value_bet = relationship("ValueBet")
