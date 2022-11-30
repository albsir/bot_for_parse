import asyncio
import json
import os
from datetime import date
import pandas as pd
from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import InvalidQueryID
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from handlers import admin
from create_bot import bot
from keyboards import client_kb
from aiogram.types import InlineKeyboardMarkup

cb_modify_search = CallbackData('post', 'msg_text')

path_to_driver = os.getcwd() + "/" + "drivers/chromedriver.exe"
path_to_clients = os.getcwd() + "/" + "json/clients"
path_to_admins_statistics = os.getcwd() + "/" + "json/admins/statistics"
path_to_admins_settings = os.getcwd() + "/" + "json/admins/settings"
path_to_admins_techsup = os.getcwd() + "/" + "json/admins/techsup"
path_to_admins_settings_ban_users = path_to_admins_settings + "/" + "ban_users.json"


class FSMClient(StatesGroup):
    begin = State()
    techsup_begin = State()
    search_begin = State()
    search_begin_message = State()
    search_begin_min_price = State()
    search_begin_max_price = State()
    searching = State()


"""

                                      РАБОТА СО СТАТИСТИКОЙ

"""


async def update_date_statistic():
    global path_to_admins_statistics
    path_to_statistics_clients = path_to_admins_statistics + "/clients.json"
    path_to_statistics_search = path_to_admins_statistics + "/search.json"
    with open(path_to_statistics_clients, 'r', encoding='utf8') as file:
        current_statistics_clients = json.load(file)
    with open(path_to_statistics_search, 'r', encoding='utf8') as file:
        current_statistics_search = json.load(file)
    current_statistics_clients["Counts_clients_all_time"] += 1
    current_date = date.today()
    if current_statistics_clients["Current_month"] != current_date.month:
        current_statistics_clients["Current_month"] = current_date.month
        current_statistics_clients["Counts_clients_current_month"] = 0
        current_statistics_clients["Times_Use_Load_File_current_month"] = 0
        for item in current_statistics_search:
            item["Times_Get_Search_current_month"] = 0
    if current_statistics_clients["Current_week_day"] != current_date.isoweekday():
        current_statistics_clients["Current_week_day"] = current_date.isoweekday()
        current_statistics_clients["Counts_clients_current_week"] = 0
        current_statistics_clients["Times_Use_Load_File_current_week"] = 0
        for item in current_statistics_search:
            item["Times_Get_Search_current_week"] = 0
    if current_statistics_clients["Current_day"] != current_date.day:
        current_statistics_clients["Current_day"] = current_date.day
        current_statistics_clients["Counts_clients_current_day"] = 0
        current_statistics_clients["Times_Use_Load_File_current_day"] = 0
        for item in current_statistics_search:
            item["Times_Get_Search_current_day"] = 0
    current_statistics_clients["Counts_clients_current_month"] += 1
    current_statistics_clients["Counts_clients_current_week"] += 1
    current_statistics_clients["Counts_clients_current_day"] += 1
    with open(path_to_statistics_clients, 'w', encoding='utf8') as file:
        json.dump(current_statistics_clients, file, ensure_ascii=False)
    with open(path_to_statistics_search, 'w', encoding='utf8') as file:
        json.dump(current_statistics_search, file, ensure_ascii=False)


async def check_member(user_id: int):
    global path_to_clients, path_to_admins_statistics
    path_to_statistics_clients = path_to_admins_statistics + "/clients.json"
    with open(path_to_statistics_clients, 'r', encoding='utf8') as file:
        current_statistics_clients = json.load(file)
    path_to_current_client = path_to_clients + "/" + str(user_id)
    if os.path.exists(path_to_current_client):
        return
    else:
        os.mkdir(path_to_current_client)
        current_statistics_clients["clients_id"].append(user_id)


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
    await update_date_statistic()
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
    await update_date_statistic()
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
    await bot.send_message(callback.from_user.id, "Введите сообщение, которое получат администраторы")
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
    await bot.send_message(callback.from_user.id, "Вводите слово")
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
    await bot.send_message(message.from_user.id, "Введите миниальный бюджет в рублях Пример: 150000")


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
    await bot.send_message(message.from_user.id, "Введите максимальный бюджет:")


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
    await callback.answer(cache_time=80)
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
    pass


async def search_begin_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_clients, path_to_admins_statistics
    path_to_statistics_search = path_to_admins_statistics + "/search.json"
    with open(path_to_statistics_search, 'r', encoding='utf8') as file:
        current_search_search = json.load(file)
    await callback.answer("Идет поиск...", cache_time=80)
    bot_answer = await bot.send_message(callback.from_user.id, "Загрузка... Ожидайте")
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
    driver = Chrome(path_to_driver)
    url = "https://zakupki.gov.ru/" \
          "epz/order/extendedsearch/results.html?searchString=" + current_client_search["message_for_search"] + \
          "&morphology=on" \
          "&search-filter=Дате+размещения&pageNumber=1&sortDirection=false&recordsPerPage=_10" \
          "&showLotsInfoHidden=false&sortBy=UPDATE_DATE"

    if current_client_search["modify_button"][0] == 1:
        url += "&fz44=on"
    if current_client_search["modify_button"][1] == 1:
        url += "&fz223=on"
    if current_client_search["modify_button"][2] == 1:
        url += "&fz94=on"
    if current_client_search["modify_button"][3] == 1:
        url += "&ppRf615=on"

    url += "&af=on&priceFromGeneral=" + str(current_client_search["price_min"]) + \
           "&priceToGeneral=" + str(current_client_search["price_max"]) + "&currencyIdGeneral=-1"
    driver.get(url)
    pages = driver.find_element(By.CLASS_NAME, "paginator.align-self-center.m-0")
    pages_new = pages.find_elements(By.CLASS_NAME, "page")
    pages_count = int(pages_new[len(pages_new) - 1].text)
    order_numbers = []
    purchase_volumes = []
    client_names = []
    begin_prices = []
    start_dates = []
    end_dates = []
    links = []
    await bot_answer.edit_text("Загрузка...")
    for page in range(pages_count):
        url = "https://zakupki.gov.ru/" \
              "epz/order/extendedsearch/results.html?searchString=" + current_client_search["message_for_search"] + \
              "&morphology=on" \
              "&search-filter=Дате+размещения&pageNumber=" + str(page + 1) + "&sortDirection=false&recordsPerPage=_10" \
                                                                             "&showLotsInfoHidden=false&sortBy=UPDATE_DATE"

        if current_client_search["modify_button"][0] == 1:
            url += "&fz44=on"
        if current_client_search["modify_button"][1] == 1:
            url += "&fz223=on"
        if current_client_search["modify_button"][2] == 1:
            url += "&fz94=on"
        if current_client_search["modify_button"][3] == 1:
            url += "&ppRf615=on"

        url += "&af=on&priceFromGeneral=" + str(current_client_search["price_min"]) + \
               "&priceToGeneral=" + str(current_client_search["price_max"]) + "&currencyIdGeneral=-1"
        driver.get(url)
        result_total = driver.find_element(By.CLASS_NAME, "search-results__total")
        try:
            result_total_int = int(result_total.text[:result_total.text.find(' ')])
        except ValueError:
            print(result_total.text)
            return
        quotes = driver.find_elements(By.CLASS_NAME, "search-registry-entry-block.box-shadow-search-input")
        for quote in quotes:
            quote_number = quote.find_element(By.CLASS_NAME, "registry-entry__header-mid__number")
            order_numbers.append(quote_number.text)
            quote_purchase_volume = quote.find_element(By.CLASS_NAME, "registry-entry__body-value")
            purchase_volumes.append(quote_purchase_volume.text)
            quote_client_name = quote.find_element(By.CLASS_NAME, "registry-entry__body-href")
            client_names.append(quote_client_name.text)
            quote_begin_price = quote.find_element(By.CLASS_NAME, "price-block__value")
            begin_prices.append(quote_begin_price.text)

            quote_second = quote.find_element(By.CLASS_NAME, "data-block.mt-auto")
            quote_dates = quote_second.find_elements(By.CLASS_NAME, "data-block__value")
            i = 0
            for quote_date in quote_dates:
                if i == 1:
                    i += 1
                elif i == 0:
                    start_dates.append(quote_date.text)
                    i += 1
                else:
                    end_dates.append(quote_date.text)
            quote_link = quote_number.find_element(By.CSS_SELECTOR, "div.registry-entry__header-mid__number [href]")
            links.append(quote_link.get_attribute('href'))
            await bot_answer.edit_text("Загружено " + str(len(order_numbers)) +
                                       " заявок из " + str(result_total_int))
            await asyncio.sleep(1)
    driver.close()
    array_for_file = []
    for i in range(len(order_numbers)):
        array_for_file.append([])
        array_for_file[i].append(order_numbers[i])
        array_for_file[i].append(purchase_volumes[i])
        array_for_file[i].append(client_names[i])
        array_for_file[i].append(begin_prices[i])
        array_for_file[i].append(start_dates[i])
        array_for_file[i].append(end_dates[i])
        stroke = '=HYPERLINK("' + links[i] + '"' + ',"ОТКРЫТЬ")'
        array_for_file[i].append(stroke)
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
        for i in range(len(order_numbers)):
            keyboard = await client_kb.answer_search_link(links[i])
            answer = "Заявка: " + order_numbers[i] + "\n" + "Объект закупки:\n" + purchase_volumes[i] + "\n" + \
                     "Заказчик:\n" + client_names[i] + "\n" + "Начальная цена: " + begin_prices[i] + " руб\n" + \
                     "Размещено: " + start_dates[i] + "\n" + "Окончание подачи заявок: " + end_dates[i] + "\n"
            await bot.send_message(callback.from_user.id,
                                   answer,
                                   reply_markup=keyboard)
            await asyncio.sleep(1)
        await cansel_handler_callback_f(callback, state)


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


"""

                                        РЕГИСТРАЦИЯ ХЕНЛДЕРОВ

"""


def register_handlers_client(dp: Dispatcher):
    # Начало
    dp.register_message_handler(answer_pre_start_f, commands="start", state=None)
    dp.register_callback_query_handler(change_menu_search_f, text='search_change_menu',
                                       state=None)
    dp.register_callback_query_handler(change_menu_admin_f, text='admin_change_menu',
                                       state=None)
    dp.register_callback_query_handler(change_menu_techsup_f, text='tech_sup_change_menu',
                                       state=None)
    dp.register_callback_query_handler(main_menu_callback_f, text='lk_change_menu',
                                       state=None)
    # Отмена
    dp.register_message_handler(back_menu_after_message_f, commands="/cansel", state="*")
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
