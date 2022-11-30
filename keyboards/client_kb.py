from aiogram.types import InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from handlers import client

fz_no = ["44-ФЗ ❌", "223-ФЗ ❌", "94-ФЗ ❌", "ПП РФ 615 ❌", "Отправить файлом ❌"]
fz_yes = ["44-ФЗ ✅", "223-ФЗ ✅", "94-ФЗ ✅", "ПП РФ 615 ✅", "Отправить файлом ✅"]


async def answer_pre_start_f():
    kb_inline = InlineKeyboardMarkup()
    b1 = InlineKeyboardButton(text='🏢 Личный кабинет', callback_data='lk_change_menu')
    b2 = InlineKeyboardButton(text='🧳 Администратор', callback_data='admin_change_menu')
    b3 = InlineKeyboardButton(text='🔎 Поиск', callback_data='search_change_menu')
    b4 = InlineKeyboardButton(text='🆘 Тех.Поддержка', callback_data='tech_sup_change_menu')

    kb_inline.row(b1, b2).row(b3).add(b4)
    return kb_inline


async def answer_start_f():
    kb_inline = InlineKeyboardMarkup()
    await answer_add_button_cansel_f(kb_inline)
    return kb_inline


async def answer_after_chose_search_f(modify: list):
    kb_inline = InlineKeyboardMarkup()
    buttons = []
    for i in range(len(modify)):
        if modify[i] == 1:
            clb_d_str = 'search_change_settings_' + str(i)
            b = InlineKeyboardButton(text=fz_yes[i], callback_data=client.cb_modify_search.new(msg_text=clb_d_str))
            buttons.append(b)
        else:
            clb_d_str = 'search_change_settings_' + str(i)
            b = InlineKeyboardButton(text=fz_no[i], callback_data=client.cb_modify_search.new(msg_text=clb_d_str))
            buttons.append(b)
    b5 = InlineKeyboardButton(text='🔎 Искать', callback_data='search_begin')
    for item in buttons:
        kb_inline.row(item)
    kb_inline.add(b5)
    await answer_add_button_cansel_f(kb_inline)
    return kb_inline


async def answer_search_link(link: str):
    kb_inline = InlineKeyboardMarkup()
    b = InlineKeyboardButton(text='🎉 Перейти', url=link)
    kb_inline.add(b)
    return kb_inline


async def answer_download_search():
    kb_inline = InlineKeyboardMarkup()
    b = InlineKeyboardButton(text='⬇ Скачать', callback_data="download_search_result")
    kb_inline.add(b)
    await answer_add_button_cansel_f(kb_inline)
    return kb_inline


async def answer_add_button_cansel_f(kb_inline):
    back = InlineKeyboardButton(text='🔄 отмена', callback_data='cansel')
    kb_inline.add(back)
