import os, json
from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from selenium.webdriver.common.by import By

from create_bot import bot
from keyboards import client_kb
from selenium.webdriver import Chrome
import pandas as pd
cb_modify_search = CallbackData('post', 'msg_text')

path_to_driver = os.getcwd() + "/" + "drivers/chromedriver.exe"
path_to_clients = os.getcwd() + "/" + "json/clients/"


class FSMClient(StatesGroup):
    begin = State()
    search_begin = State()
    searching = State()


"""

                                        РАБОТА С МЕНЮ

"""


async def main_menu_message_f(message: types.Message, state: FSMContext):
    keyboard = await client_kb.answer_start_f()
    await bot.send_message(message.from_user.id, "Меню", reply_markup=keyboard)
    pass


async def main_menu_callback_f(callback: types.CallbackQuery, state: FSMContext):
    keyboard = await client_kb.answer_start_f()
    await bot.send_message(callback.from_user.id, "Меню", reply_markup=keyboard)
    await callback.answer()


async def back_menu_after_message_f(message: types.Message, state: FSMContext):
    await state.finish()
    await main_menu_message_f(message, state)


async def cansel_handler_callback_f(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.answer("Возврат в начальное меню")
    await main_menu_callback_f(callback, state)


"""

                                        РАБОТА С РАЗДЕЛОМ МЕНЮ: ПОИСК

"""


async def change_menu_search_f(callback: types.CallbackQuery, state: FSMContext):
    await FSMClient.search_begin.set()
    await bot.send_message(callback.from_user.id, "Вводите слово")
    await callback.answer()


async def search_after_get_message_f(message: types.Message, state: FSMContext):
    global path_to_clients
    begin_modify = {"modify_button": [0, 0, 0, 0], "message_for_search": message.text}
    try:
        path_to_current_client = path_to_clients + str(message.from_user.id)
        os.mkdir(path_to_current_client)
    except FileExistsError:
        path_to_current_client = path_to_clients + str(message.from_user.id)
    path_to_current_client += "/search.json"
    with open(path_to_current_client, 'w', encoding='cp1251') as file:
        json.dump(begin_modify, file, ensure_ascii=False)
    keyboard = await client_kb.answer_after_chose_search_f(begin_modify["modify_button"])
    await bot.send_message(message.from_user.id, "Выберите какие пункты должны быть включены и нажмите кнопку поиск",
                           reply_markup=keyboard)


async def search_chose_buttons_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_clients
    id_modify = callback.data
    id_modify = id_modify[id_modify.rfind('_') + 1:]
    id_modify_int = int(id_modify)
    path_to_current_client = path_to_clients + str(callback.from_user.id) + "/search.json"
    with open(path_to_current_client, 'r', encoding='cp1251') as file:
        current_client_search = json.load(file)

    if current_client_search["modify_button"][id_modify_int] == 0:
        current_client_search["modify_button"][id_modify_int] = 1
    else:
        current_client_search["modify_button"][id_modify_int] = 0
    with open(path_to_current_client, 'w', encoding='cp1251') as file:
        json.dump(current_client_search, file, ensure_ascii=False)
    keyboard = await client_kb.answer_after_chose_search_f(current_client_search["modify_button"])
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()
    pass


async def search_begin_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_clients
    print("a")
    await FSMClient.searching.set()
    await callback.answer("Идет поиск...")
    path_to_current_client = path_to_clients + str(callback.from_user.id) + "/search.json"
    with open(path_to_current_client, 'r', encoding='cp1251') as file:
        current_client_search = json.load(file)
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
    url += "af=on&ca=on&pc=on&pa=on&currencyIdGeneral=-1"
    driver.get(url)
    quotes = driver.find_elements(By.CLASS_NAME, "search-registry-entry-block.box-shadow-search-input")
    total = []
    for quote in quotes:
        quote_new = quote.find_element(By.CLASS_NAME, "registry-entry__header-mid__number")
        total.append(quote_new.text)
    #df = pd.DataFrame(total, columns=[])
    driver.close()
    print(total)
    await cansel_handler_callback_f(callback, state)


"""

                                        РЕГИСТРАЦИЯ ХЕНЛДЕРОВ

"""


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(main_menu_message_f, commands="start", state=None)
    dp.register_callback_query_handler(change_menu_search_f, text='search_change_menu',
                                       state=None)
    dp.register_message_handler(search_after_get_message_f, commands=None, state=FSMClient.search_begin)
    dp.register_callback_query_handler(search_chose_buttons_f, cb_modify_search.filter(),
                                       state=FSMClient.search_begin)
    dp.register_callback_query_handler(search_begin_f, text='search_begin',
                                       state=FSMClient.search_begin)
