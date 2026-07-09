from aiogram import types

from bot import dp
from bot.keyboards.inline import get_settings_keyboard
from database import SessionLocal
from database.crud import get_user, update_user_settings


@dp.callback_query(lambda c: c.data.startswith("settings:"))
async def callback_settings(callback_query: types.CallbackQuery):
    """Обработчик настроек"""
    action = callback_query.data.split(":")[1]

    if action == "show":
        await show_settings(callback_query)
    elif action == "toggle_notify":
        await toggle_notifications(callback_query)
    elif action == "threshold":
        await cycle_threshold(callback_query)


async def show_settings(callback_query: types.CallbackQuery):
    """Показать настройки пользователя"""
    telegram_id = callback_query.from_user.id

    db = SessionLocal()
    try:
        user = get_user(db, telegram_id)
        if not user:
            text = "❌ Профиль не найден. Отправьте /start для регистрации."
            await callback_query.message.edit_text(text)
            await callback_query.answer()
            return

        text = (
            "⚙️ **Настройки уведомлений:**\n\n"
            f"📊 Текущий порог value: **{user.min_value_threshold*100:.0f}%**\n"
            f"🔔 Уведомления: **{'включены' if user.notify_value_bets else 'выключены'}**\n\n"
            "Измени настройки кнопками ниже 👇"
        )

        settings = {
            "notify_value_bets": user.notify_value_bets,
            "min_value_threshold": user.min_value_threshold,
        }

    finally:
        db.close()

    await callback_query.message.edit_text(
        text,
        reply_markup=get_settings_keyboard(settings)
    )
    await callback_query.answer()


async def toggle_notifications(callback_query: types.CallbackQuery):
    """Переключить уведомления"""
    telegram_id = callback_query.from_user.id

    db = SessionLocal()
    try:
        user = get_user(db, telegram_id)
        if user:
            new_value = not user.notify_value_bets
            update_user_settings(db, telegram_id, notify_value_bets=new_value)
            status = "включены" if new_value else "выключены"
            text = f"✅ Уведомления **{status}**"
        else:
            text = "❌ Профиль не найден"
    finally:
        db.close()

    await callback_query.answer(text, show_alert=True)
    await show_settings(callback_query)


async def cycle_threshold(callback_query: types.CallbackQuery):
    """Переключить порог value"""
    telegram_id = callback_query.from_user.id
    thresholds = [0.03, 0.05, 0.08, 0.10, 0.15]

    db = SessionLocal()
    try:
        user = get_user(db, telegram_id)
        if user:
            current = user.min_value_threshold
            next_threshold = thresholds[0]
            for i, t in enumerate(thresholds):
                if t == current and i + 1 < len(thresholds):
                    next_threshold = thresholds[i + 1]
                    break

            update_user_settings(db, telegram_id, min_value_threshold=next_threshold)
            text = f"✅ Порог value изменён на **{next_threshold*100:.0f}%**"
        else:
            text = "❌ Профиль не найден"
    finally:
        db.close()

    await callback_query.answer(text, show_alert=True)
    await show_settings(callback_query)
