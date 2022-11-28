import datetime
import json
import os
from json import JSONDecodeError
from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import CantParseEntities, CantInitiateConversation, BadRequest
from create_bot import bot


class FSMClient(StatesGroup):
    begin = State()


async def main_menu_message_f(message: types.Message, state: FSMContext):

    pass


async def main_menu_callback_f(callback: types.CallbackQuery, state: FSMContext):
    pass


async def back_menu_after_message_f(message: types.Message, state: FSMContext):
    await state.finish()
    await main_menu_message_f(message, state)


async def cansel_handler_callback_f(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.answer("Возврат в начальное меню")
    await main_menu_callback_f(callback, state)


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(main_menu_message_f, commands="start", state=None)
