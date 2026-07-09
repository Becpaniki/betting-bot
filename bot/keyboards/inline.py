from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚽ Виды спорта", callback_data="sport:all"),
            InlineKeyboardButton(text="💰 Value-ставки", callback_data="value:show"),
        ],
        [
            InlineKeyboardButton(text="📊 Сравнение коэффициентов", callback_data="odds:compare"),
            InlineKeyboardButton(text="🔮 Прогнозы", callback_data="predictions:show"),
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings:show"),
        ],
    ])
    return keyboard


def get_sports_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора вида спорта"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚽ Футбол", callback_data="sport:football"),
            InlineKeyboardButton(text="🏀 Баскетбол", callback_data="sport:basketball"),
        ],
        [
            InlineKeyboardButton(text="🏒 Хоккей", callback_data="sport:hockey"),
            InlineKeyboardButton(text="🎾 Теннис", callback_data="sport:tennis"),
        ],
        [
            InlineKeyboardButton(text="🎮 Киберспорт", callback_data="sport:esports"),
            InlineKeyboardButton(text="📋 Все виды", callback_data="sport:all"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main"),
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
