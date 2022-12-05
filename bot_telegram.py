# -*- coding:utf -8 -*-
import datetime
from aiogram.utils import executor
from create_bot import dp
from handlers import client, admin
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
from handlers import parsing


async def mailing():
    scheduler.pause()
    files = os.listdir(path_to_parsing)
    for name_file in files:
        await parsing.mail_parsing(name_file)
    scheduler.resume()


async def on_startup(_):
    print('Бот вкл  ' + str(datetime.datetime.now()))
    scheduler.add_job(mailing, 'interval', minutes=30)
    scheduler.start()
    client.scheduler = scheduler
path_to_parsing = os.getcwd() + "/" + "json/parsing"
scheduler = AsyncIOScheduler()
client.register_handlers_client(dp)
admin.register_handlers_client(dp)
executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
