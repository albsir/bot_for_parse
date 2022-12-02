import asyncio
import json
import os
import pandas as pd
from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import InvalidQueryID

from create_bot import bot
from keyboards import admin_kb

cb_clients_request_techsup = CallbackData('post', 'msg_text')
cb_client_list_requests_techsup = CallbackData('post', 'msg_text')

path_to_clients = os.getcwd() + "/" + "json/clients"
path_to_admins_statistics = os.getcwd() + "/" + "json/admins/statistics"
path_to_admins_settings = os.getcwd() + "/" + "json/admins/settings"
path_to_admins_techsup = os.getcwd() + "/" + "json/admins/techsup"
path_to_admins_settings_in_bot = path_to_admins_settings + "/" + "option_in_bot.json"
path_to_admins_settings_ban_users = path_to_admins_settings + "/" + "ban_users.json"


class FSMAdmin(StatesGroup):
    begin = State()
    send_mes_begin = State()
    statistics_begin = State()
    techsup_begin = State()
    techsup_chose_request_begin = State()
    techsup_chose_request_end = State()


"""

                                        РАБОТА С МЕНЮ

"""


async def main_menu_message_f(message: types.Message, state: FSMContext):
    await FSMAdmin.begin.set()
    keyboard = await admin_kb.answer_start_f()
    await bot.send_message(message.from_user.id, "Меню", reply_markup=keyboard)
    pass


async def main_menu_callback_f(callback: types.CallbackQuery, state: FSMContext):
    await FSMAdmin.begin.set()
    keyboard = await admin_kb.answer_start_f()
    await bot.send_message(callback.from_user.id, "Меню", reply_markup=keyboard)
    try:
        await callback.answer()
    except InvalidQueryID:
        pass


"""

                                        РАБОТА С РАЗДЕЛОМ МЕНЮ: РАЗОСЛАТЬ ВСЕМ СМС

"""


async def change_menu_send_all_user_message_f(callback: types.CallbackQuery, state: FSMContext):
    await FSMAdmin.send_mes_begin.set()
    await bot.send_message(callback.from_user.id, "Напишите сообщение, которое нужно всем отправить")


async def send_mes_after_enter_f(message: types.Message, state: FSMContext):
    global path_to_admins_statistics
    path_to_statistics_clients = path_to_admins_statistics + "/clients.json"
    with open(path_to_statistics_clients, 'r', encoding='utf8') as file:
        current_statistics_clients = json.load(file)
    bot_answer = await bot.send_message(message.from_user.id, "Отправка началась, ожидайте завершения")
    for user in current_statistics_clients["clients_id"]:
        if user != message.from_user.id:
            await bot.send_message(user, message.text)
            await asyncio.sleep(1)
    await bot_answer.edit_text("Отправка завершена")
    await main_menu_message_f(message, state)


"""

                                        РАБОТА С РАЗДЕЛОМ МЕНЮ: Статистика

"""


async def change_menu_statistics(callback: types.CallbackQuery, state: FSMContext):
    await FSMAdmin.statistics_begin.set()
    keyboard = await admin_kb.answer_change_statistics()
    await bot.send_message(callback.from_user.id, "Выберите статистику", reply_markup=keyboard)
    await callback.answer()


async def change_stat_request(callback: types.CallbackQuery, state: FSMContext):
    global path_to_admins_statistics
    path_to_statistics_search = path_to_admins_statistics + "/search.json"
    with open(path_to_statistics_search, 'r', encoding='utf8') as file:
        current_statistics_search = json.load(file)
    bot_answer = await bot.send_message(callback.from_user.id, "Подгружаю статистику, ожидайте")
    array_for_file = []
    for item in current_statistics_search:
        array_for_file.append([])
        modify_len_array = len(array_for_file) - 1
        array_for_file[modify_len_array].append(item["Name_Search"])
        array_for_file[modify_len_array].append(item["Times_Get_Search_current_day"])
        array_for_file[modify_len_array].append(item["Times_Get_Search_current_week"])
        array_for_file[modify_len_array].append(item["Times_Get_Search_current_month"])
        array_for_file[modify_len_array].append(item["Times_Get_Search_all_time"])
    df = pd.DataFrame(array_for_file, columns=['Слово', 'за день', 'за неделю', 'за месяц',
                                               'за все время'])
    with pd.ExcelWriter('result.xlsx') as writer:
        df.to_excel(writer, sheet_name='my_analysis', index=False, na_rep='NaN')
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['my_analysis'].set_column(col_idx, col_idx, column_width)
    await bot.delete_message(bot_answer.chat.id, bot_answer.message_id)
    await callback.message.answer_document(open('result.xlsx', 'rb'))
    os.remove('result.xlsx')
    await main_menu_callback_f(callback, state)


async def change_stat_clients(callback: types.CallbackQuery, state: FSMContext):
    global path_to_admins_statistics
    path_to_statistics_clients = path_to_admins_statistics + "/clients.json"
    with open(path_to_statistics_clients, 'r', encoding='utf8') as file:
        current_statistics_clients = json.load(file)
    answer = "Кол-во клиентов за день:  " + str(current_statistics_clients["Counts_clients_current_day"]) + \
             "\nКол-во клиентов за неделю:  " + str(current_statistics_clients["Counts_clients_current_week"]) + \
             "\nКол-во клиентов за месяц:  " + str(current_statistics_clients["Counts_clients_current_month"]) + \
             "\nКол-во клиентов за все время:  " + str(current_statistics_clients["Counts_clients_all_time"]) + \
             "\nКол-во клиентов, скачавших запрос файлом  за день:  " + \
             str(current_statistics_clients["Times_Use_Load_File_current_day"]) + \
             "\nКол-во клиентов, скачавших запрос файлом  за неделю:  " + \
             str(current_statistics_clients["Times_Use_Load_File_current_week"]) + \
             "\nКол-во клиентов, скачавших запрос файлом за месяц:  " + \
             str(current_statistics_clients["Times_Use_Load_File_current_month"]) + \
             "\nКол-во клиентов, скачавших запрос файлом за все время:  " + \
             str(current_statistics_clients["Times_Use_Load_File_all_time"]) + \
             "\nКол-во клиентов, перешли по ссылке за день:  " + \
             str(current_statistics_clients["Times_Use_Load_Link_current_day"]) + \
             "\nКол-во клиентов, перешли по ссылке за неделю:  " + \
             str(current_statistics_clients["Times_Use_Load_Link_current_week"]) + \
             "\nКол-во клиентов, перешли по ссылке за месяц:  " + \
             str(current_statistics_clients["Times_Use_Load_Link_current_month"]) + \
             "\nКол-во клиентов, перешли по ссылке за все время:  " + \
             str(current_statistics_clients["Times_Use_Load_Link_all_time"])
    await bot.send_message(callback.from_user.id, answer)
    bot_answer = await bot.send_message(callback.from_user.id, "Переход в главное меню...")
    await asyncio.sleep(3)
    await bot.delete_message(bot_answer.chat.id, bot_answer.message_id)
    await main_menu_callback_f(callback, state)


async def admin_check_requests_add_tender_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_admins_statistics
    path_to_statistics_tender_links = path_to_admins_statistics + "/tender_links.json"
    with open(path_to_statistics_tender_links, 'r', encoding='utf8') as file:
        current_statistics_tender_links = json.load(file)
    answer = ""
    for key, value in current_statistics_tender_links.items():
        answer += "Ссылка: " + str(key) + "\nотправлялась: " + str(value) + " раз\n"
    if answer == "":
        await bot.send_message(callback.from_user.id, "Результат:\nПусто")
        await callback.answer()
        await main_menu_callback_f(callback, state)
    else:
        await bot.send_message(callback.from_user.id, "Результат:\n" + answer)
        await callback.answer()
        await main_menu_callback_f(callback, state)

"""

                                РАБОТА С РАЗДЕЛОМ МЕНЮ: Разослать всем сообещние


"""


async def send_all_admins_about_new_request_f():
    global path_to_admins_settings
    path_to_admins_id = path_to_admins_settings + "/" + "admins_id.json"
    with open(path_to_admins_id, 'r', encoding='utf8') as file:
        current_admins_id = json.load(file)
    for item in current_admins_id:
        await bot.send_message(item["id"], "Новый запрос в техподдержку")
        await asyncio.sleep(0.3)


"""

                                        РАБОТА С РАЗДЕЛОМ МЕНЮ: ТехПоддержка

"""


async def change_menu_techsup_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_admins_settings_in_bot
    await FSMAdmin.techsup_begin.set()

    with open(path_to_admins_settings_in_bot, 'r', encoding='utf8') as file:
        current_admin_options_in_bot = json.load(file)

    keyboard = await admin_kb.answer_change_techsup(current_admin_options_in_bot["page_for_techsup_users"])
    await bot.send_message(callback.from_user.id, "Выберите пользователя", reply_markup=keyboard)
    await callback.answer()


async def answer_next_techsup_users(callback: types.CallbackQuery, state: FSMContext):
    global path_to_admins_settings_in_bot
    with open(path_to_admins_settings_in_bot, 'r', encoding='utf8') as file:
        current_admin_options_in_bot = json.load(file)
    current_admin_options_in_bot["page_for_techsup_users"] += 1
    with open(path_to_admins_settings_in_bot, 'w', encoding='utf8') as file:
        json.dump(current_admin_options_in_bot, file, ensure_ascii=False)
    answer_kb = await admin_kb.answer_change_techsup(current_admin_options_in_bot["page_for_techsup_users"])
    await bot.send_message(callback.from_user.id, 'Выберите Пользователя', reply_markup=answer_kb)
    await callback.answer()


async def answer_back_techsup_users(callback: types.CallbackQuery, state: FSMContext):
    global path_to_admins_settings_in_bot
    with open(path_to_admins_settings_in_bot, 'r', encoding='utf8') as file:
        current_admin_options_in_bot = json.load(file)
    current_admin_options_in_bot["page_for_techsup_users"] -= 1
    with open(path_to_admins_settings_in_bot, 'w', encoding='utf8') as file:
        json.dump(current_admin_options_in_bot, file, ensure_ascii=False)
    answer_kb = await admin_kb.answer_change_techsup(current_admin_options_in_bot["page_for_techsup_users"])
    await bot.send_message(callback.from_user.id, 'Выберите Пользователя', reply_markup=answer_kb)
    await callback.answer()


async def after_change_user_techsup_f(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    global path_to_admins_settings_in_bot
    await FSMAdmin.techsup_chose_request_begin.set()

    with open(path_to_admins_settings_in_bot, 'r', encoding='utf8') as file:
        current_admin_options_in_bot = json.load(file)
    current_admin_options_in_bot['current_user_for_techsup'] = int(callback_data['msg_text'])
    with open(path_to_admins_settings_in_bot, 'w', encoding='utf8') as file:
        json.dump(current_admin_options_in_bot, file, ensure_ascii=False)
    keyboard = await admin_kb.answer_change_user_requests_techsup(
        current_admin_options_in_bot["page_for_techsup_request"],
        current_admin_options_in_bot['current_user_for_techsup'])
    await bot.send_message(callback.from_user.id, "Выберите запрос", reply_markup=keyboard)
    await callback.answer()


async def answer_next_requests_techsup_users(callback: types.CallbackQuery, state: FSMContext):
    global path_to_admins_settings_in_bot
    with open(path_to_admins_settings_in_bot, 'r', encoding='utf8') as file:
        current_admin_options_in_bot = json.load(file)
    current_admin_options_in_bot["page_for_techsup_request"] += 1
    with open(path_to_admins_settings_in_bot, 'w', encoding='utf8') as file:
        json.dump(current_admin_options_in_bot, file, ensure_ascii=False)
    answer_kb = await admin_kb.answer_change_user_requests_techsup(
        current_admin_options_in_bot["page_for_techsup_request"],
        current_admin_options_in_bot['current_user_for_techsup'])
    await bot.send_message(callback.from_user.id, 'Выберите запрос', reply_markup=answer_kb)
    await callback.answer()


async def answer_back_requests_techsup_users(callback: types.CallbackQuery, state: FSMContext):
    global path_to_admins_settings_in_bot
    with open(path_to_admins_settings_in_bot, 'r', encoding='utf8') as file:
        current_admin_options_in_bot = json.load(file)
    current_admin_options_in_bot["page_for_techsup_request"] -= 1
    with open(path_to_admins_settings_in_bot, 'w', encoding='utf8') as file:
        json.dump(current_admin_options_in_bot, file, ensure_ascii=False)
    answer_kb = await admin_kb.answer_change_user_requests_techsup(
        current_admin_options_in_bot["page_for_techsup_request"],
        current_admin_options_in_bot['current_user_for_techsup'])
    await bot.send_message(callback.from_user.id, 'Выберите запрос', reply_markup=answer_kb)
    await callback.answer()


async def after_change_request_user_techsup_f(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    global path_to_admins_settings_in_bot, path_to_admins_techsup
    await FSMAdmin.techsup_chose_request_end.set()
    answer = ""
    with open(path_to_admins_settings_in_bot, 'r', encoding='utf8') as file:
        current_admin_options_in_bot = json.load(file)
    path_to_admins_techsup_requests = path_to_admins_techsup + "/"
    path_to_admins_techsup_requests += str(current_admin_options_in_bot["current_user_for_techsup"]) + ".json"
    with open(path_to_admins_techsup_requests, 'r', encoding='utf8') as file:
        current_user_requests = json.load(file)
    current_admin_options_in_bot["current_request_message_id"] = int(callback_data['msg_text'])
    with open(path_to_admins_settings_in_bot, 'w', encoding='utf8') as file:
        json.dump(current_admin_options_in_bot, file, ensure_ascii=False)
    for item in current_user_requests:
        if item["message_id"] == int(callback_data['msg_text']):
            answer = str(item["text"])
    keyboard = await admin_kb.chose_option_request_user_f()
    await bot.send_message(callback.from_user.id, "Вопрос пользователя:\n" + answer +
                           "\nНапишите ответ:", reply_markup=keyboard)
    await callback.answer()


async def answer_ban_request_user_techsup_f(callback: types.CallbackQuery, state: FSMContext):
    global path_to_admins_settings_in_bot, path_to_admins_settings_ban_users, path_to_admins_techsup
    with open(path_to_admins_settings_in_bot, 'r', encoding='utf8') as file:
        current_admin_options_in_bot = json.load(file)
    with open(path_to_admins_settings_ban_users, 'r', encoding='utf8') as file:
        current_admin_options_ban_users = json.load(file)
    path_to_admins_techsup_requests = path_to_admins_techsup + "/"
    path_to_admins_techsup_requests += str(current_admin_options_in_bot["current_user_for_techsup"]) + ".json"
    current_admin_options_ban_users.append(current_admin_options_in_bot["current_user_for_techsup"])
    os.remove(path_to_admins_techsup_requests)
    await bot.send_message(callback.from_user.id, "Пользователь забанен")
    await main_menu_callback_f(callback, state)


async def answer_skip_request_user_techsup_f(callback: types.CallbackQuery, state: FSMContext):
    await delete_request_user()
    await bot.send_message(callback.from_user.id, "Запрос был удален")
    await main_menu_callback_f(callback, state)


async def answer_request_user_techsup_f(message: types.Message, state: FSMContext):
    global path_to_admins_settings_in_bot, path_to_admins_techsup
    with open(path_to_admins_settings_in_bot, 'r', encoding='utf8') as file:
        current_admin_options_in_bot = json.load(file)
    path_to_admins_techsup_requests = path_to_admins_techsup + "/"
    path_to_admins_techsup_requests += str(current_admin_options_in_bot["current_user_for_techsup"]) + ".json"
    with open(path_to_admins_techsup_requests, 'r', encoding='utf8') as file:
        current_user_requests = json.load(file)
    question = ""
    for item in current_user_requests:
        if item["message_id"] == current_admin_options_in_bot["current_request_message_id"]:
            question = item["text"]
            break
    answer = "На ваш вопрос:\n" + question + "\nАдминистратор ответил:\n" + message.text
    await bot.send_message(current_admin_options_in_bot["current_user_for_techsup"], answer)
    await delete_request_user()
    await main_menu_message_f(message, state)


async def delete_request_user():
    global path_to_admins_techsup, path_to_admins_settings_in_bot
    with open(path_to_admins_settings_in_bot, 'r', encoding='utf8') as file:
        current_admin_options_in_bot = json.load(file)
    path_to_admins_techsup_requests = path_to_admins_techsup + "/"
    path_to_admins_techsup_requests += str(current_admin_options_in_bot["current_user_for_techsup"]) + ".json"
    with open(path_to_admins_techsup_requests, 'r', encoding='utf8') as file:
        current_user_requests = json.load(file)
    for item in current_user_requests:
        if item["message_id"] == current_admin_options_in_bot["current_request_message_id"]:
            current_user_requests.remove(item)
            break
    with open(path_to_admins_techsup_requests, 'w', encoding='utf8') as file:
        json.dump(current_user_requests, file, ensure_ascii=False)


"""

                                        РЕГИСТРАЦИЯ ХЕНЛДЕРОВ

"""


def register_handlers_client(dp: Dispatcher):
    # работа с отправкой сообщений всем
    dp.register_callback_query_handler(change_menu_send_all_user_message_f, text='admin_send_mes_all_user_change_menu',
                                       state=FSMAdmin.begin)
    dp.register_message_handler(send_mes_after_enter_f, commands=None, state=FSMAdmin.send_mes_begin)

    # работа с статистикой
    dp.register_callback_query_handler(change_menu_statistics, text='admin_statistics_change_menu',
                                       state=FSMAdmin.begin)
    dp.register_callback_query_handler(change_stat_request, text='admin_stat_requests',
                                       state=FSMAdmin.statistics_begin)
    dp.register_callback_query_handler(change_stat_clients, text='admin_stat_clients',
                                       state=FSMAdmin.statistics_begin)
    dp.register_callback_query_handler(admin_check_requests_add_tender_f, text='admin_check_requests_add_tender',
                                       state=FSMAdmin.statistics_begin)
    # Работа с техподдержкой
    dp.register_callback_query_handler(change_menu_techsup_f, text='admin_tech_sup_change_menu',
                                       state=FSMAdmin.begin)
    dp.register_callback_query_handler(answer_next_techsup_users, text='next_techsup_users',
                                       state=FSMAdmin.techsup_begin)
    dp.register_callback_query_handler(answer_back_techsup_users, text='back_techsup_users',
                                       state=FSMAdmin.techsup_begin)
    dp.register_callback_query_handler(after_change_user_techsup_f, cb_clients_request_techsup.filter(),
                                       state=FSMAdmin.techsup_begin)
    dp.register_callback_query_handler(answer_next_requests_techsup_users, text='next_techsup_user_requests',
                                       state=FSMAdmin.techsup_chose_request_begin)
    dp.register_callback_query_handler(answer_back_requests_techsup_users, text='back_techsup_user_requests',
                                       state=FSMAdmin.techsup_chose_request_begin)
    dp.register_callback_query_handler(after_change_request_user_techsup_f, cb_client_list_requests_techsup.filter(),
                                       state=FSMAdmin.techsup_chose_request_begin)
    dp.register_callback_query_handler(answer_ban_request_user_techsup_f, text='admin_ban_user_after_request_techsup',
                                       state=FSMAdmin.techsup_chose_request_end)
    dp.register_callback_query_handler(answer_skip_request_user_techsup_f, text='admin_skip_request_techsup',
                                       state=FSMAdmin.techsup_chose_request_end)
    dp.register_message_handler(answer_request_user_techsup_f, commands=None, state=FSMAdmin.techsup_chose_request_end)
