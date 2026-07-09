from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔥 Матчи дня", callback_data="matches:today"),
        ],
    ])
    return keyboard


def get_settings_keyboard(user_settings: dict = None) -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    if user_settings is None:
        user_settings = {
            "notify_value_bets": True,
            "min_value_threshold": 0.05,
        }

    notify_text = "✅ Уведомления включены" if user_settings.get("notify_value_bets") else "❌ Уведомления выключены"
    threshold = user_settings.get("min_value_threshold", 0.05)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=notify_text, callback_data="settings:toggle_notify"),
        ],
        [
            InlineKeyboardButton(text=f"📊 Порог value: {threshold*100}%", callback_data="settings:threshold"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main"),
        ],
    ])
    return keyboard
