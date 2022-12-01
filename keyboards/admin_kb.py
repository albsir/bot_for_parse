from aiogram.types import InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from handlers import admin
import json
import os
from itertools import islice

path_to_admins_techsup = os.getcwd() + "/" + "json/admins/techsup"


async def answer_start_f():
    kb_inline = InlineKeyboardMarkup()
    b1 = InlineKeyboardButton(text='📮 Разослать всем сообещние', callback_data='admin_send_mes_all_user_change_menu')
    b2 = InlineKeyboardButton(text='📲 Тех.Поддержка заявки', callback_data='admin_tech_sup_change_menu')
    b3 = InlineKeyboardButton(text='📜 Статистика', callback_data='admin_statistics_change_menu')
    kb_inline.add(b1).add(b2).add(b3)
    await answer_add_button_cansel_f(kb_inline)
    return kb_inline


async def answer_change_statistics():
    kb_inline = InlineKeyboardMarkup()
    b1 = InlineKeyboardButton(text='📈 Статистика по запросам', callback_data='admin_stat_requests')
    b2 = InlineKeyboardButton(text='📊 Статистика по клиентам', callback_data='admin_stat_clients')
    b3 = InlineKeyboardButton(text='📊 Добавление тендеров', callback_data='admin_check_requests_add_tender')
    kb_inline.add(b1).add(b2).add(b3)
    await answer_add_button_cansel_f(kb_inline)
    return kb_inline


async def answer_change_techsup(page: int):
    global path_to_admins_techsup
    kb_inline = InlineKeyboardMarkup()
    users = os.listdir(path_to_admins_techsup)
    i = page * 6
    if i == 0:
        next_b = InlineKeyboardButton(text='вперед ➥', callback_data='next_techsup_users')
        count_buttons = 2
        kb_inline.add(next_b)
    elif i >= len(users) - 1:
        back = InlineKeyboardButton(text='🔙 назад', callback_data='back_techsup_users')
        count_buttons = 2
        kb_inline.add(back)
    else:
        back = InlineKeyboardButton(text='🔙 назад', callback_data='back_techsup_users')
        next_b = InlineKeyboardButton(text='вперед ➥', callback_data='next_techsup_users')
        kb_inline.row(back, next_b)
        count_buttons = 3
    break_all = False
    for user_file in users:
        with open(path_to_admins_techsup + "/" + user_file, 'r', encoding='utf8') as file:
            current_user_techsup = json.load(file)
        for item in current_user_techsup:
            b = InlineKeyboardButton(text=str(item['chat']['id']),
                                     callback_data=admin.cb_clients_request_techsup.new(
                                         msg_text=str(item['chat']['id'])))
            kb_inline.add(b)
            i += 1
            if i > len(users) - 1:
                break_all = True
                break
            count_buttons += 1
            if count_buttons == 9:
                break_all = True
                break
        if break_all:
            break
    await answer_add_button_cansel_f(kb_inline)
    return kb_inline


async def answer_change_user_requests_techsup(page: int, user_id: int):
    global path_to_admins_techsup
    kb_inline = InlineKeyboardMarkup()
    users = os.listdir(path_to_admins_techsup)
    i = page * 6
    count_buttons = 0
    if i == 0:
        next_b = InlineKeyboardButton(text='вперед ➥', callback_data='next_techsup_user_requests')
        count_buttons += 2
        kb_inline.add(next_b)
    elif i >= len(users) - 1:
        back = InlineKeyboardButton(text='🔙 назад', callback_data='back_techsup_user_requests')
        count_buttons += 2
        kb_inline.add(back)
    else:
        back = InlineKeyboardButton(text='🔙 назад', callback_data='back_techsup_user_requests')
        next_b = InlineKeyboardButton(text='вперед ➥', callback_data='next_techsup_user_requests')
        kb_inline.row(back, next_b)
        count_buttons += 3
    path_to_current_techsup_user = path_to_admins_techsup + "/" + str(user_id) + ".json"
    with open(path_to_current_techsup_user, 'r', encoding='utf8') as file:
        current_user_techsup = json.load(file)
    for item in current_user_techsup:
        b = InlineKeyboardButton(text="📌 Запрос №" + str(item['message_id']),
                                 callback_data=admin.cb_client_list_requests_techsup.new(
                                     msg_text=str(item['message_id'])))
        kb_inline.add(b)
        i += 1
        if i > len(users) - 1:
            break
        count_buttons += 1
        if count_buttons == 9:
            break
    await answer_add_button_cansel_f(kb_inline)
    return kb_inline


async def chose_option_request_user_f():
    kb_inline = InlineKeyboardMarkup()
    b1 = InlineKeyboardButton(text='🚫 Забанить', callback_data='admin_ban_user_after_request_techsup')
    b2 = InlineKeyboardButton(text='🚪 Пропустить', callback_data='admin_skip_request_techsup')
    kb_inline.add(b1).add(b2)
    await answer_add_button_cansel_f(kb_inline)
    return kb_inline


async def answer_add_button_cansel_f(kb_inline):
    back = InlineKeyboardButton(text='🔄 отмена', callback_data='cansel')
    kb_inline.add(back)
