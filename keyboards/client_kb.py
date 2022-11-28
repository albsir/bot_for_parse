from aiogram.types import InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton


async def answer_start(kb_inline):
    return kb_inline


async def answer_cansel(kb_inline):
    back = InlineKeyboardButton(text='🔙 отмена', callback_data='cansel')
    kb_inline.add(back)
    return kb_inline
