from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models import User, Match, Odds, ValueBet, Notification


# ==================== User CRUD ====================

def get_user(db: Session, telegram_id: int) -> Optional[User]:
    """Получить пользователя по Telegram ID"""
    return db.query(User).filter(User.telegram_id == telegram_id).first()


def create_user(db: Session, telegram_id: int, username: str = None, first_name: str = None) -> User:
    """Создать нового пользователя"""
    user = User(telegram_id=telegram_id, username=username, first_name=first_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_settings(db: Session, telegram_id: int, **kwargs) -> Optional[User]:
    """Обновить настройки пользователя"""
    user = get_user(db, telegram_id)
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user


# ==================== Match CRUD ====================

def get_or_create_match(db: Session, external_id: str, sport: str, team_home: str, team_away: str, **kwargs) -> Match:
    """Получить или создать матч"""
    match = db.query(Match).filter(Match.external_id == external_id).first()
    if not match:
        match = Match(
            external_id=external_id,
            sport=sport,
            team_home=team_home,
            team_away=team_away,
            **kwargs
        )
        db.add(match)
        db.commit()
        db.refresh(match)
    return match


def get_matches_by_sport(db: Session, sport: str, limit: int = 50) -> List[Match]:
    """Получить матчи по виду спорта"""
    return db.query(Match)\
        .filter(Match.sport == sport)\
        .order_by(desc(Match.start_time))\
        .limit(limit)\
        .all()


# ==================== Odds CRUD ====================

def create_odds(db: Session, match_id: int, bookmaker: str, **kwargs) -> Odds:
    """Создать запись коэффициентов"""
    odds = Odds(match_id=match_id, bookmaker=bookmaker, **kwargs)
    db.add(odds)
    db.commit()
    db.refresh(odds)
    return odds


def get_latest_odds_for_match(db: Session, match_id: int) -> List[Odds]:
    """Получить последние коэффициенты для матча"""
    return db.query(Odds)\
        .filter(Odds.match_id == match_id)\
        .order_by(desc(Odds.parsed_at))\
        .all()


def get_odds_by_bookmaker(db: Session, bookmaker: str, limit: int = 100) -> List[Odds]:
    """Получить коэффициенты по букмекеру"""
    return db.query(Odds)\
        .filter(Odds.bookmaker == bookmaker)\
        .order_by(desc(Odds.parsed_at))\
        .limit(limit)\
        .all()


# ==================== ValueBet CRUD ====================

def create_value_bet(db: Session, match_id: int, bookmaker: str, outcome: str,
                     odds: float, fair_odds: float, value_percentage: float, probability: float) -> ValueBet:
    """Создать value-ставку"""
    value_bet = ValueBet(
        match_id=match_id,
        bookmaker=bookmaker,
        outcome=outcome,
        odds=odds,
        fair_odds=fair_odds,
        value_percentage=value_percentage,
        probability=probability
    )
    db.add(value_bet)
    db.commit()
    db.refresh(value_bet)
    return value_bet


def get_unnotified_value_bets(db: Session, min_value: float = 0.05) -> List[ValueBet]:
    """Получить неуведомленные value-ставки"""
    return db.query(ValueBet)\
        .filter(ValueBet.notified == False, ValueBet.value_percentage >= min_value)\
        .order_by(desc(ValueBet.value_percentage))\
        .all()


def mark_value_bet_notified(db: Session, value_bet_id: int):
    """Пометить value-ставку как уведомленную"""
    value_bet = db.query(ValueBet).filter(ValueBet.id == value_bet_id).first()
    if value_bet:
        value_bet.notified = True
        db.commit()


# ==================== Notification CRUD ====================

def create_notification(db: Session, user_id: int, value_bet_id: int) -> Notification:
    """Создать уведомление"""
    notification = Notification(user_id=user_id, value_bet_id=value_bet_id)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
