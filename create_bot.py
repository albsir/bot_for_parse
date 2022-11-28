from aiogram import Bot
from aiogram.dispatcher import Dispatcher
import os, json
from aiogram.contrib.fsm_storage.memory import MemoryStorage




path_to_option_bot = os.getcwd() + "/" + "settings.json"


storage = MemoryStorage()
with open(path_to_option_bot, 'r', encoding='cp1251') as file:
    option_bot = json.load(file)
api_bot = option_bot["api_bot"]
bot = Bot(token=api_bot)
dp = Dispatcher(bot, storage=storage)
