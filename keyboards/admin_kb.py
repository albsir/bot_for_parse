import json, os
from handlers import admin
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from itertools import islice

path_for_chats_options = os.getcwd() + "/" + "json/chats/options/"
texts_to_keyboards_json_for_bot_path = os.getcwd() + "/" + "json/option_for_bot/texts_to_keyboards.json"
path_for_admins_options = os.getcwd() + "/" + "json/admins/options/"


async def answer_start(kb_inline: InlineKeyboardMarkup):
    for filename in os.listdir(path_for_chats_options):
        try:
            with open(os.path.join(path_for_chats_options, filename) + "/options.json", 'r', encoding='cp1251') as file:
                option_for_chat = json.load(file)
            for item in option_for_chat:
                kb_inline.add(InlineKeyboardButton(text=item["name"],
                                                   callback_data=admin.cb_chats.new(msg_text=item["name"])))
        except:
            pass
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(back)
    return kb_inline


async def answer_after_choose_chat(kb_inline: InlineKeyboardMarkup):
    ch1 = InlineKeyboardButton(text='Слова', callback_data='kb_admin_menu_words')
    ch2 = InlineKeyboardButton(text='Ссылки', callback_data='kb_admin_menu_links')
    ch3 = InlineKeyboardButton(text='Блокировка', callback_data='kb_admin_menu_bans')
    ch4 = InlineKeyboardButton(text='Хештеги', callback_data='kb_admin_menu_hashtags')
    ch5 = InlineKeyboardButton(text='Текст', callback_data='kb_admin_menu_texts')
    ch6 = InlineKeyboardButton(text='Подписки на каналы', callback_data='kb_admin_menu_subscription')
    ch7 = InlineKeyboardButton(text='Правила чата', callback_data='kb_admin_menu_rules')
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.row(ch1, ch2).row(ch3, ch4).row(ch5, ch6).add(ch7).add(back)
    return kb_inline


async def answer_chapter_rules(kb_inline: InlineKeyboardMarkup):
    a1 = InlineKeyboardButton(text='Посмотреть ссылку\nна правила', callback_data='kb_admin_check_link_rules_chat')
    a2 = InlineKeyboardButton(text='Изменить ссылку\nна правила', callback_data='kb_admin_change_link_rules_chat')
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(a1).add(a2).add(back)
    return kb_inline


async def answer_chapter_subscription(kb_inline: InlineKeyboardMarkup):
    a1 = InlineKeyboardButton(text='Список каналов', callback_data='kb_admin_list_links_subscription')
    a2 = InlineKeyboardButton(text='Добавить новый канал', callback_data='kb_admin_add_link_subscription')
    a3 = InlineKeyboardButton(text='Удалить канал', callback_data='kb_admin_delete_link_subscription')
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(a1).add(a2).add(a3).add(back)
    return kb_inline


async def answer_delete_subscription(kb_inline: InlineKeyboardMarkup, chat_id: int):
    global path_for_admins_options, path_for_chats_options

    path_for_current_chats_options = path_for_chats_options + str(chat_id) + "/options.json"
    with open(path_for_current_chats_options, 'r', encoding='cp1251') as file:
        chat_options = json.load(file)
    for item in chat_options:
        for channel in item["need_channels_subscription"]:
            name_channel = str(channel)
            name_channel = name_channel[name_channel.rfind('/') + 1:]
            kb_inline.add(InlineKeyboardButton(text=name_channel,
                                               callback_data=admin.cb_channels.new(msg_text=name_channel)))
        back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
        kb_inline.add(back)
        return kb_inline


async def answer_chapter_words(kb_inline: InlineKeyboardMarkup):
    a1 = InlineKeyboardButton(text='Список запрещенных слов', callback_data='kb_admin_list_ban_words')
    a2 = InlineKeyboardButton(text='Добавить новое запрещенное слово', callback_data='kb_admin_add_ban_word')
    a3 = InlineKeyboardButton(text='Удалить запрещенное слово', callback_data='kb_admin_delete_ban_word')
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(a1).add(a2).add(a3).add(back)
    return kb_inline


async def answer_chapter_links(kb_inline: InlineKeyboardMarkup):
    a1 = InlineKeyboardButton(text='Список разрешенных ссылок', callback_data='kb_admin_list_links')
    a2 = InlineKeyboardButton(text='Добавить разрешенную ссылку', callback_data='kb_admin_add_link')
    a3 = InlineKeyboardButton(text='Удалить разрешенную ссылку', callback_data='kb_admin_delete_link')
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(a1).add(a2).add(a3).add(back)
    return kb_inline


async def answer_chapter_bans(kb_inline: InlineKeyboardMarkup):
    a1 = InlineKeyboardButton(text='Посмотреть время в бане пользователей',
                              callback_data='kb_admin_list_time_to_ban_human')
    a2 = InlineKeyboardButton(text='Изменить время в бане пользователя',
                              callback_data='kb_admin_change_time_to_ban_human')
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(a1).add(a2).add(back)
    return kb_inline


async def answer_chapter_hashtags(kb_inline: InlineKeyboardMarkup):
    a1 = InlineKeyboardButton(text='С фото', callback_data='kb_admin_menu_hashtags_with_photo')
    a2 = InlineKeyboardButton(text='Без фото', callback_data='kb_admin_menu_hashtags_without_photo')
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(a1).add(a2).add(back)
    return kb_inline


async def answer_chapter_hashtags_with_photo(kb_inline: InlineKeyboardMarkup):
    a1 = InlineKeyboardButton(text='Список разрешенных хештегов с фото',
                              callback_data='kb_admin_list_hashtag_with_photo')
    a2 = InlineKeyboardButton(text='Добавить новый хештег с фото', callback_data='kb_admin_add_hashtag_with_photo')
    a3 = InlineKeyboardButton(text='Удалить разрешенный хэштег с фото',
                              callback_data='kb_admin_remove_hashtag_with_photo')
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(a1).add(a2).add(a3).add(back)
    return kb_inline


async def answer_chapter_hashtags_without_photo(kb_inline: InlineKeyboardMarkup):
    a1 = InlineKeyboardButton(text='Список разрешенных хештегов без фото',
                              callback_data='kb_admin_list_hashtag_without_photo')
    a2 = InlineKeyboardButton(text='Добавить новый хештег без фото', callback_data='kb_admin_add_hashtag_without_photo')
    a3 = InlineKeyboardButton(text='Удалить разрешенный хэштег без фото',
                              callback_data='kb_admin_remove_hashtag_without_photo')
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(a1).add(a2).add(a3).add(back)
    return kb_inline


async def answer_chapter_texts(kb_inline: InlineKeyboardMarkup):
    a1 = InlineKeyboardButton(text='Посмотреть отправляемый текст', callback_data='kb_admin_viewing_send_texts')
    a2 = InlineKeyboardButton(text='Изменить отправляемый текст', callback_data='kb_admin_change_send_texts')
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(a1).add(a2).add(back)
    return kb_inline


async def answer_viewing_text(kb_inline: InlineKeyboardMarkup, page: int):
    global texts_to_keyboards_json_for_bot_path
    with open(texts_to_keyboards_json_for_bot_path, 'r', encoding='cp1251') as file:
        array_texts_to_keyboards = json.load(file)
    # 0..5 6..11 12..17
    i = page * 6
    if i == 0:
        next = InlineKeyboardButton(text=' вперед', callback_data='next_viewing_text')
        count_buttons = 2
        kb_inline.add(next)
    elif i >= len(array_texts_to_keyboards) - 1:
        back = InlineKeyboardButton(text='🔙 назад', callback_data='back_viewing_text')
        count_buttons = 2
        kb_inline.add(back)
    else:
        back = InlineKeyboardButton(text='🔙 назад', callback_data='back_viewing_text')
        next = InlineKeyboardButton(text=' вперед', callback_data='next_viewing_text')
        kb_inline.row(back, next)
        count_buttons = 3
    for key, value in islice(array_texts_to_keyboards.items(), i, None):
        kb_inline.add(InlineKeyboardButton(text=str(key),
                                           callback_data=admin.cb_texts.new(msg_text=str(value))
                                           )
                      )
        i += 1
        if i > len(array_texts_to_keyboards) - 1:
            break
        count_buttons += 1
        if count_buttons == 9:
            break
    cansel = InlineKeyboardButton(text=' отмена', callback_data='cansel')
    kb_inline.add(cansel)
    return kb_inline


async def answer_choose_user_for_change_time_to_ban(kb_inline: InlineKeyboardMarkup):
    a1 = InlineKeyboardButton(text='Добавить время (в минутах)', callback_data='kb_admin_add_time_to_ban')
    a2 = InlineKeyboardButton(text='Уменьшить время (в минутах)', callback_data='kb_admin_reduce_time_to_ban')
    a3 = InlineKeyboardButton(text='Убрать блокировку', callback_data='kb_admin_unban')
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.row(a1, a2).add(a3).add(back)
    return kb_inline


async def answer_cansel(kb_inline: InlineKeyboardMarkup):
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(back)
    return kb_inline
