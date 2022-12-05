import asyncio
import json
import os
from datetime import date
import pandas as pd
from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import InvalidQueryID
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from selenium.webdriver import Chrome
from urlvalidator import URLValidator, ValidationError
from handlers import admin
from create_bot import bot
from keyboards import client_kb
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from handlers import parsing

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')
cb_modify_search = CallbackData('post', 'msg_text')

path_to_driver = os.getcwd() + "/" + "drivers/chromedriver.exe"
path_to_clients = os.getcwd() + "/" + "json/clients"
path_to_admins_statistics = os.getcwd() + "/" + "json/admins/statistics"
path_to_admins_settings = os.getcwd() + "/" + "json/admins/settings"
path_to_admins_techsup = os.getcwd() + "/" + "json/admins/techsup"
path_to_admins_settings_ban_users = path_to_admins_settings + "/" + "ban_users.json"
path_to_parsing = os.getcwd() + "/" + "json/parsing"
service_chrome = Service(path_to_driver)

scheduler = AsyncIOScheduler()

class FSMClient(StatesGroup):
    begin = State()
    techsup_begin = State()
    search_begin = State()
    search_begin_message = State()
    search_begin_min_price = State()
    search_begin_max_price = State()
    searching = State()
    add_tender_place_begin = State()


"""

                                      РАБОТА СО СТАТИСТИКОЙ

"""


async def update_date_statistic(chat_id: int):
    global path_to_admins_statistics
    path_to_statistics_clients = path_to_admins_statistics + "/clients.json"
    path_to_statistics_search = path_to_admins_statistics + "/search.json"
    with open(path_to_statistics_clients, 'r', encoding='utf8') as file:
        current_statistics_clients = json.load(file)
    with open(path_to_statistics_search, 'r', encoding='utf8') as file:
        current_statistics_search = json.load(file)
    current_date = date.today()
    if current_statistics_clients["Current_month"] != current_date.month:
        current_statistics_clients["Current_month"] = current_date.month
        current_statistics_clients["Counts_clients_current_month"] = 0
        current_statistics_clients["Times_Use_Load_File_current_month"] = 0
        current_statistics_clients["Times_Use_Load_Link_current_month"] = 0
        current_statistics_clients["clients_id_current_month"].clear()
        for item in current_statistics_search:
            item["Times_Get_Search_current_month"] = 0
    if current_statistics_clients["Current_week_day"] == 7 and current_date.isoweekday() == 1:
        current_statistics_clients["Current_week_day"] = current_date.isoweekday()
        current_statistics_clients["Counts_clients_current_week"] = 0
        current_statistics_clients["Times_Use_Load_File_current_week"] = 0
        current_statistics_clients["Times_Use_Load_Link_current_week"] = 0
        current_statistics_clients["clients_id_current_week"].clear()
        for item in current_statistics_search:
            item["Times_Get_Search_current_week"] = 0
    elif current_statistics_clients["Current_week_day"] != current_date.isoweekday():
        current_statistics_clients["Current_week_day"] = current_date.isoweekday()
    if current_statistics_clients["Current_day"] != current_date.day:
        current_statistics_clients["Current_day"] = current_date.day
        current_statistics_clients["Counts_clients_current_day"] = 0
        current_statistics_clients["Times_Use_Load_File_current_day"] = 0
        current_statistics_clients["Times_Use_Load_Link_current_day"] = 0
        current_statistics_clients["clients_id_current_day"].clear()
        for item in current_statistics_search:
            item["Times_Get_Search_current_day"] = 0

    new_id = True
    for client_id in current_statistics_clients["clients_id_all_time"]:
        if chat_id == client_id:
            new_id = False
            break
    if new_id:
        current_statistics_clients["Counts_clients_all_time"] += 1
        current_statistics_clients["clients_id_all_time"].append(chat_id)

    new_id = True
    for client_id in current_statistics_clients["clients_id_current_month"]:
        if chat_id == client_id:
            new_id = False
            break
    if new_id:
        current_statistics_clients["Counts_clients_current_month"] += 1
        current_statistics_clients["clients_id_current_month"].append(chat_id)

    new_id = True
    for client_id in current_statistics_clients["clients_id_current_week"]:
        if chat_id == client_id:
            new_id = False
            break
    if new_id:
        current_statistics_clients["Counts_clients_current_week"] += 1
        current_statistics_clients["clients_id_current_week"].append(chat_id)

    new_id = True
    for client_id in current_statistics_clients["clients_id_current_day"]:
        if chat_id == client_id:
            new_id = False
            break
    if new_id:
        current_statistics_clients["Counts_clients_current_day"] += 1
        current_statistics_clients["clients_id_current_day"].append(chat_id)

    with open(path_to_statistics_clients, 'w', encoding='utf8') as file:
        json.dump(current_statistics_clients, file, ensure_ascii=False)
    with open(path_to_statistics_search, 'w', encoding='utf8') as file:
        json.dump(current_statistics_search, file, ensure_ascii=False)


"""

                                        РАБОТА С МЕНЮ

"""


async def answer_pre_start_f(message: types.Message, state: FSMContext):
    global path_to_clients, path_to_admins_settings_ban_users
    with open(path_to_admins_settings_ban_users, 'r', encoding='utf8') as file:
        current_admin_options_ban_users = json.load(file)
    for user_id in current_admin_options_ban_users:
        if user_id == message.chat.id:
            await bot.send_message(message.chat.id, "Вы забанены")
            return
    await update_date_statistic(message.chat.id)
    keyboard = await client_kb.answer_pre_start_f()
    await bot.send_message(message.chat.id, "Выбирайте", reply_markup=keyboard)


async def main_menu_callback_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_admins_settings_ban_users, path_to_clients
    with open(path_to_admins_settings_ban_users, 'r', encoding='utf8') as file:
        current_admin_options_ban_users = json.load(file)
    for user_id in current_admin_options_ban_users:
        if user_id == callback.from_user.id:
            await bot.send_message(callback.from_user.id, "Вы забанены")
            return
    await update_date_statistic(callback.from_user.id)
    keyboard = await client_kb.answer_start_f()
    await bot.send_message(callback.from_user.id, "Меню:", reply_markup=keyboard)
    try:
        await callback.answer()
    except InvalidQueryID:
        pass


async def back_menu_after_message_f(message: types.Message, state: FSMContext):
    await state.finish()
    await answer_pre_start_f(message, state)


async def cansel_handler_callback_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_clients
    if await state.get_state() == FSMClient.searching.state:
        try:
            path_to_current_client = path_to_clients + "/" + str(callback.from_user.id) + "/search.json"
            with open(path_to_current_client, 'r', encoding='utf8') as file:
                current_client_search = json.load(file)
            path_client_result = path_to_clients + "/" + str(callback.from_user.id) + "/"
            path_client_result += current_client_search["message_for_search"] + '.xlsx'
            os.remove(path_client_result)
        except:
            pass
    await state.finish()
    try:
        await callback.answer("Возврат в начальное меню")
    except InvalidQueryID:
        pass
    await answer_pre_start_f(callback.message, state)


"""

                                        РАБОТА С РАЗДЕЛОМ МЕНЮ: АДМИН


"""


async def change_menu_admin_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_admins_settings
    path_to_admins_accounts = path_to_admins_settings + "/" + "accounts.json"
    path_to_admins_id = path_to_admins_settings + "/" + "admins_id.json"
    with open(path_to_admins_accounts, 'r', encoding='utf8') as file:
        current_admins_accounts = json.load(file)
    for user in current_admins_accounts:
        if user == callback.from_user.username:
            with open(path_to_admins_id, 'r', encoding='utf8') as file:
                current_admins_id = json.load(file)
            for user_admin in current_admins_id:
                if user_admin["id"] == callback.from_user.id:
                    await admin.main_menu_callback_f(callback, state)
                    return
            current_admins_id.append({"name": user, "id": callback.from_user.id})
            with open(path_to_admins_id, 'w', encoding='utf8') as file:
                json.dump(current_admins_id, file, ensure_ascii=False)
            await admin.main_menu_callback_f(callback, state)
            return
    await bot.send_message(callback.from_user.id, "У вас нет доступа")
    await cansel_handler_callback_f(callback, state)


"""

                                        РАБОТА С РАЗДЕЛОМ МЕНЮ: ТехПоддержка


"""


async def change_menu_techsup_f(callback: types.CallbackQuery, state: FSMContext):
    await FSMClient.techsup_begin.set()
    keyboard = InlineKeyboardMarkup()
    await client_kb.answer_add_button_cansel_f(keyboard)
    await bot.send_message(callback.from_user.id, "Введите сообщение, которое получат администраторы",
                           reply_markup=keyboard)
    await callback.answer()


async def get_request_techsup_after_message_f(message: types.Message, state: FSMContext):
    global path_to_admins_techsup
    path_to_admins_techsup_requests = path_to_admins_techsup + "/" + str(message.from_user.id) + ".json"
    try:
        with open(path_to_admins_techsup_requests, 'r', encoding='utf8') as file:
            current_admins_techsup_requests = json.load(file)
    except FileNotFoundError:
        current_admins_techsup_requests = []
    message_to_json = json.loads(message.as_json())
    current_admins_techsup_requests.append(message_to_json)
    with open(path_to_admins_techsup_requests, 'w', encoding='utf8') as file:
        json.dump(current_admins_techsup_requests, file, ensure_ascii=False)
    await admin.send_all_admins_about_new_request_f()
    await bot.send_message(message.chat.id, "Запрос отправлен, ожидайте ответа")
    await asyncio.sleep(1)
    await back_menu_after_message_f(message, state)


"""

                                        РАБОТА С РАЗДЕЛОМ МЕНЮ: ПОИСК

"""


async def change_menu_search_f(callback: types.CallbackQuery, state: FSMContext):
    await FSMClient.search_begin.set()
    keyboard = InlineKeyboardMarkup()
    await client_kb.answer_add_button_cansel_f(keyboard)
    await bot.send_message(callback.from_user.id,
                           "Введите ключевое слово для поиска тендера\nПример №1: арматура\nПример №2: пшеница"
                           "\nПример №3: перевозка\nПример №4: ремонт",
                           reply_markup=keyboard)
    await callback.answer()


async def search_after_get_message_f(message: types.Message, state: FSMContext):
    await FSMClient.search_begin_message.set()
    global path_to_clients
    begin_modify = {"modify_button": [0, 0, 0, 0, 0], "message_for_search": message.text, "price_min": 0,
                    "price_max": 0}
    try:
        path_to_current_client = path_to_clients + "/" + str(message.from_user.id)
        os.mkdir(path_to_current_client)
    except FileExistsError:
        path_to_current_client = path_to_clients + "/" + str(message.from_user.id)
    path_to_current_client += "/search.json"
    with open(path_to_current_client, 'w', encoding='utf8') as file:
        json.dump(begin_modify, file, ensure_ascii=False)
    keyboard = InlineKeyboardMarkup()
    await client_kb.answer_add_button_cansel_f(keyboard)
    await bot.send_message(message.from_user.id, "Введите миниальный бюджет в рублях Пример: 150000",
                           reply_markup=keyboard)


async def search_after_get_min_price_f(message: types.Message, state: FSMContext):
    await FSMClient.search_begin_min_price.set()
    global path_to_clients
    path_to_current_client = path_to_clients + "/" + str(message.from_user.id)
    path_to_current_client += "/search.json"
    with open(path_to_current_client, 'r', encoding='utf8') as file:
        current_client_search = json.load(file)
    try:
        current_client_search["price_min"] = int(message.text.replace(' ', ''))
        with open(path_to_current_client, 'w', encoding='utf8') as file:
            json.dump(current_client_search, file, ensure_ascii=False)
    except:
        await bot.send_message(message.from_user.id, "Вы неправильно ввели мин бюджет, попробуйте снова:")
        await search_after_get_message_f(message, state)
    keyboard = InlineKeyboardMarkup()
    await client_kb.answer_add_button_cansel_f(keyboard)
    await bot.send_message(message.from_user.id, "Введите максимальный бюджет в рублях Пример: 250000",
                           reply_markup=keyboard)


async def search_after_get_max_price_f(message: types.Message, state: FSMContext):
    await FSMClient.search_begin_max_price.set()
    global path_to_clients
    path_to_current_client = path_to_clients + "/" + str(message.from_user.id)
    path_to_current_client += "/search.json"
    with open(path_to_current_client, 'r', encoding='utf8') as file:
        current_client_search = json.load(file)
    try:
        current_client_search["price_max"] = int(message.text.replace(' ', ''))
        with open(path_to_current_client, 'w', encoding='utf8') as file:
            json.dump(current_client_search, file, ensure_ascii=False)
        keyboard = await client_kb.answer_after_chose_search_f(current_client_search["modify_button"])
        await bot.send_message(message.from_user.id,
                               "Выберите какие пункты должны быть включены и нажмите кнопку поиск\nРЕКОМЕНДУЕМ" +
                               " включить опцию <загрузить файлом>, если, по вашему запросу, может быть много заявок",
                               reply_markup=keyboard)
    except:
        await bot.send_message(message.from_user.id, "Вы неправильно ввели мax бюджет, попробуйте снова:")
        await search_after_get_min_price_f(message, state)


async def search_chose_buttons_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_clients
    id_modify = callback.data
    id_modify = id_modify[id_modify.rfind('_') + 1:]
    id_modify_int = int(id_modify)
    path_to_current_client = path_to_clients + "/" + str(callback.from_user.id) + "/search.json"
    with open(path_to_current_client, 'r', encoding='utf8') as file:
        current_client_search = json.load(file)
    if current_client_search["modify_button"][id_modify_int] == 0:
        current_client_search["modify_button"][id_modify_int] = 1
    else:
        current_client_search["modify_button"][id_modify_int] = 0
    with open(path_to_current_client, 'w', encoding='utf8') as file:
        json.dump(current_client_search, file, ensure_ascii=False)
    keyboard = await client_kb.answer_after_chose_search_f(current_client_search["modify_button"])
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


async def search_begin_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_clients, path_to_admins_statistics
    path_to_statistics_search = path_to_admins_statistics + "/search.json"
    with open(path_to_statistics_search, 'r', encoding='utf8') as file:
        current_search_search = json.load(file)
    scheduler.pause()
    bot_answer = await bot.send_message(callback.from_user.id, "Загрузка из Zakupki ... Ожидайте")
    bot_answer2 = await bot.send_message(callback.from_user.id, "Загрузка из Sber ... Ожидайте")
    await FSMClient.searching.set()
    path_to_current_client = path_to_clients + "/" + str(callback.from_user.id) + "/search.json"
    with open(path_to_current_client, 'r', encoding='utf8') as file:
        current_client_search = json.load(file)
    have_name_search = False
    for item in current_search_search:
        if item["Name_Search"] == current_client_search["message_for_search"]:
            item["Times_Get_Search_all_time"] += 1
            item["Times_Get_Search_current_month"] += 1
            item["Times_Get_Search_current_week"] += 1
            item["Times_Get_Search_current_day"] += 1
            have_name_search = True
    if not have_name_search:
        current_search_search.append({"Name_Search": current_client_search["message_for_search"],
                                      "Times_Get_Search_all_time": 1,
                                      "Times_Get_Search_current_month": 1,
                                      "Times_Get_Search_current_week": 1,
                                      "Times_Get_Search_current_day": 1})
    with open(path_to_statistics_search, 'w', encoding='utf8') as file:
        json.dump(current_search_search, file, ensure_ascii=False)
    print(path_to_driver)
    await callback.answer("Начат поиск", cache_time=80)

    array_for_file1 = []
    array_for_file2 = []
    driver = Chrome(executable_path=path_to_driver, options=options, service=service_chrome)
    task1 = asyncio.create_task(parsing.parsing_zakupki(driver, array_for_file1, callback, bot_answer))
    driver2 = Chrome(executable_path=path_to_driver, options=options, service=service_chrome)
    task2 = asyncio.create_task(parsing.parsing_sber(driver2, array_for_file2, callback, bot_answer2))
    await task1
    await task2
    while not task1.done() and not task2.done():
        print("a")
    array_for_file = list(array_for_file1 + array_for_file2)

    if current_client_search["modify_button"][4] == 1:
        df = pd.DataFrame(array_for_file, columns=['Заявка №', 'Объект закупки', 'Заказчик', 'Начальная цена',
                                                   'Дата размещения', 'Окончание подачи заявок', 'Ссылка на заявку'])
        path_client_result = path_to_clients + "/" + str(callback.from_user.id) + "/"
        path_client_result += current_client_search["message_for_search"] + '.xlsx'
        with pd.ExcelWriter(path_client_result) as writer:
            df.to_excel(writer, sheet_name='my_analysis', index=False, na_rep='NaN')
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                writer.sheets['my_analysis'].set_column(col_idx, col_idx, column_width)
        keyboard = await client_kb.answer_download_search()
        await bot.send_message(callback.from_user.id, "Файл загружен", reply_markup=keyboard)
    else:
        for i in range(len(array_for_file)):
            stroke = array_for_file[i][6]
            stroke = stroke[stroke.find('"') + 1:]
            stroke = stroke[:stroke.find('"')]
            keyboard = await client_kb.answer_search_link(stroke)
            answer = "*Заявка*: " + array_for_file[i][0] + "\n*Объект закупки*: " + array_for_file[i][1] + \
                     "\n*Заказчик*: " + array_for_file[i][2] + "\n*Начальная цена*: " + array_for_file[i][3] + \
                     "\n*Размещено*: " + array_for_file[i][4] + "\n*Окончание подачи заявок*: " \
                     + array_for_file[i][5] + "\n"
            await bot.send_message(callback.from_user.id,
                                   answer,
                                   reply_markup=keyboard, parse_mode="Markdown")
            await asyncio.sleep(1)
    try:
        driver.quit()
    finally:
        pass
    try:
        driver2.quit()
    finally:
        pass
    path_to_current_client_parsing = path_to_parsing + "/" + str(callback.from_user.id) + ".json"
    try:
        with open(path_to_current_client_parsing, 'r', encoding='utf8') as file:
            current_client_parsing = json.load(file)
        current_index_message_and_active = 0
        have_tender = False
        for i in range(len(array_for_file)):
            if current_client_search["message_for_search"] == current_client_parsing["active_tenders"]:
                current_index_message_and_active = i
                have_tender = True
                break
        if have_tender:
            for i in range(len(array_for_file)):
                have_tender_view_yet = False
                for k in range(len(current_client_search["tenders_view_yet"][current_index_message_and_active])):
                    if array_for_file[i][0] == \
                            current_client_search["tenders_view_yet"][current_index_message_and_active][k]:
                        have_tender_view_yet = True
                        break
                if not have_tender_view_yet:
                    current_client_search["tenders_view_yet"][current_index_message_and_active].append(
                        array_for_file[i][0])
        else:
            current_client_parsing["active_tenders"].append(current_client_search["message_for_search"])
            current_client_parsing["zakon"].append(current_client_search["modify_button"])
            current_client_parsing["prices"].append(
                [current_client_search["price_min"], current_client_search["price_max"]])
            current_client_parsing["tenders_view_yet"].append([])
            for i in range(len(array_for_file)):
                current_client_parsing["tenders_view_yet"][-1].append(array_for_file[i][0])
    except FileNotFoundError:
        current_client_parsing = {"active_tenders": [current_client_search["message_for_search"]],
                                  "tenders_view_yet": [], "zakon": [], "prices": [[current_client_search["price_min"],
                                                                                   current_client_search["price_max"]]]}
        current_client_parsing["zakon"].append(current_client_search["modify_button"])
        current_client_parsing["tenders_view_yet"].append([])
        for i in range(len(array_for_file)):
            current_client_parsing["tenders_view_yet"][0].append(array_for_file[i][0])
    scheduler.resume()
    with open(path_to_current_client_parsing, 'w', encoding='utf8') as file:
        json.dump(current_client_parsing, file, ensure_ascii=False)


async def download_search_file_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_clients, path_to_admins_statistics
    path_to_statistics_clients = path_to_admins_statistics + "/clients.json"
    with open(path_to_statistics_clients, 'r', encoding='utf8') as file:
        current_statistics_clients = json.load(file)
    current_statistics_clients["Times_Use_Load_File_all_time"] += 1
    current_statistics_clients["Times_Use_Load_File_current_month"] += 1
    current_statistics_clients["Times_Use_Load_File_current_week"] += 1
    current_statistics_clients["Times_Use_Load_File_current_day"] += 1
    with open(path_to_statistics_clients, 'w', encoding='utf8') as file:
        json.dump(current_statistics_clients, file, ensure_ascii=False)
    path_to_current_client = path_to_clients + "/" + str(callback.from_user.id) + "/search.json"
    with open(path_to_current_client, 'r', encoding='utf8') as file:
        current_client_search = json.load(file)
    path_client_result = path_to_clients + "/" + str(callback.from_user.id) + "/"
    path_client_result += current_client_search["message_for_search"] + '.xlsx'
    await callback.message.answer_document(open(path_client_result, 'rb'))
    os.remove(path_client_result)
    await callback.answer()
    await cansel_handler_callback_f(callback, state)


async def load_link_search_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_clients, path_to_admins_statistics
    path_to_statistics_clients = path_to_admins_statistics + "/clients.json"
    with open(path_to_statistics_clients, 'r', encoding='utf8') as file:
        current_statistics_clients = json.load(file)
    current_statistics_clients["Times_Use_Load_Link_all_time"] += 1
    current_statistics_clients["Times_Use_Load_Link_current_month"] += 1
    current_statistics_clients["Times_Use_Load_Link_current_week"] += 1
    current_statistics_clients["Times_Use_Load_Link_current_day"] += 1
    with open(path_to_statistics_clients, 'w', encoding='utf8') as file:
        json.dump(current_statistics_clients, file, ensure_ascii=False)
    await callback.answer()
    await cansel_handler_callback_f(callback, state)


async def unsub_tender(callback: types.CallbackQuery, state: FSMContext):
    global path_to_parsing
    path_to_current_client_parsing = path_to_parsing + "/" + str(callback.from_user.id) + ".json"
    tender_name = callback.message.text
    tender_name = tender_name[tender_name.find(':') + 2:]
    tender_name = tender_name[:tender_name.find("новая") - 2]
    with open(path_to_current_client_parsing, 'r', encoding='utf8') as file:
        current_client_parsing = json.load(file)
    for i in range(len(current_client_parsing["active_tenders"])):
        if tender_name in current_client_parsing["active_tenders"][i]:
            current_client_parsing["active_tenders"].pop(i)
            current_client_parsing["tenders_view_yet"].pop(i)
            current_client_parsing["zakon"].pop(i)
            current_client_parsing["prices"].pop(i)
            with open(path_to_current_client_parsing, 'w', encoding='utf8') as file:
                json.dump(current_client_parsing, file, ensure_ascii=False)
            break
    await callback.answer("Вы отписались от обновления тендера: ", tender_name)
    await cansel_handler_callback_f(callback, state)


"""

                                        РАБОТА С РАЗДЕЛОМ МЕНЮ: Добавить тендерную площадку

"""


async def add_tender_place_change_menu_f(callback: types.CallbackQuery, state: FSMContext):
    await FSMClient.add_tender_place_begin.set()
    keyboard = InlineKeyboardMarkup()
    await client_kb.answer_add_button_cansel_f(keyboard)
    await bot.send_message(callback.from_user.id, "Отправьте ссылку на тендерную площадку", reply_markup=keyboard)
    await callback.answer()


async def add_tender_place_get_link_f(message: types.Message, state: FSMContext):
    global path_to_admins_statistics
    path_to_tender_links = path_to_admins_statistics + "/" + "tender_links.json"
    validate = URLValidator()
    try:
        validate(message.text)
        try:
            with open(path_to_tender_links, 'r', encoding='utf8') as file:
                current_tender_links = json.load(file)
        except FileNotFoundError:
            current_tender_links = {}
            with open(path_to_tender_links, 'w', encoding='utf8') as file:
                json.dump(current_tender_links, file, ensure_ascii=False)
        if message.text in current_tender_links:
            current_tender_links[message.text] += 1
        else:
            current_tender_links[message.text] = 1
        with open(path_to_tender_links, 'w', encoding='utf8') as file:
            json.dump(current_tender_links, file, ensure_ascii=False)
        await bot.send_message(message.chat.id, "Тендер добавлен, спасибо")
        await back_menu_after_message_f(message, state)
    except ValidationError as vlderr:
        await bot.send_message(message.chat.id, "Вы указали неккоректную ссылку")
        await back_menu_after_message_f(message, state)


"""

                                        РЕГИСТРАЦИЯ ХЕНЛДЕРОВ

"""


def register_handlers_client(dp: Dispatcher):
    # Начало
    dp.register_message_handler(answer_pre_start_f, commands="start", state="*")
    dp.register_callback_query_handler(change_menu_search_f, text='search_change_menu',
                                       state=None)
    dp.register_callback_query_handler(change_menu_admin_f, text='admin_change_menu',
                                       state=None)
    dp.register_callback_query_handler(change_menu_techsup_f, text='tech_sup_change_menu',
                                       state=None)
    dp.register_callback_query_handler(main_menu_callback_f, text='lk_change_menu',
                                       state=None)
    dp.register_callback_query_handler(add_tender_place_change_menu_f, text='add_tender_place_change_menu',
                                       state=None)
    # Отмена
    dp.register_message_handler(back_menu_after_message_f, commands="cansel", state="*")
    dp.register_callback_query_handler(cansel_handler_callback_f, text='cansel',
                                       state="*")
    # Работа с тех поддержкой
    dp.register_message_handler(get_request_techsup_after_message_f, commands=None, state=FSMClient.techsup_begin)

    # Работа с поиском
    dp.register_message_handler(search_after_get_message_f, commands=None, state=FSMClient.search_begin)
    dp.register_message_handler(search_after_get_min_price_f, commands=None, state=FSMClient.search_begin_message)
    dp.register_message_handler(search_after_get_max_price_f, commands=None, state=FSMClient.search_begin_min_price)
    dp.register_callback_query_handler(search_chose_buttons_f, cb_modify_search.filter(),
                                       state=FSMClient.search_begin_max_price)
    dp.register_callback_query_handler(search_begin_f, text='search_begin',
                                       state=FSMClient.search_begin_max_price)
    dp.register_callback_query_handler(download_search_file_f, text='download_search_result',
                                       state=FSMClient.searching)
    dp.register_callback_query_handler(load_link_search_f, text='load_link_search_result',
                                       state=FSMClient.searching)
    dp.register_callback_query_handler(unsub_tender, text='load_link_search_result_unsub',
                                       state="*")
    # Работа с добавлением тендера
    dp.register_message_handler(add_tender_place_get_link_f, commands=None, state=FSMClient.add_tender_place_begin)
