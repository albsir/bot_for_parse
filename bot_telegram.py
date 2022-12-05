# -*- coding:utf -8 -*-
import datetime
import random

from aiogram.utils import executor
from create_bot import dp
from handlers import client, admin
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
from handlers import parsing

path_to_parsing = os.getcwd() + "/" + "json/parsing"
minutes_rand = random.randint(15, 30)


async def mailing():
    global minutes_rand
    minutes_rand = random.randint(15, 30)
    scheduler.pause()
    files = os.listdir(path_to_parsing)
    for name_file in files:
        await parsing.mail_parsing(name_file)
    scheduler.resume()


async def on_startup(_):
    print('Бот вкл  ' + str(datetime.datetime.now()))
    scheduler.add_job(mailing, 'interval', minutes=minutes_rand)
    scheduler.start()
    client.scheduler = scheduler


scheduler = AsyncIOScheduler()
client.register_handlers_client(dp)
admin.register_handlers_client(dp)
executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
