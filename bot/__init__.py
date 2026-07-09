from aiogram import Bot, Dispatcher
from config import config
from aiogram.client.default import DefaultBotProperties

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
