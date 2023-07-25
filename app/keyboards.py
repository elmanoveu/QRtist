import logging
from io import BytesIO
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def start_kb():
    keyboard = InlineKeyboardMarkup()
    qr_button = InlineKeyboardButton("Сгенерировать QR-код", callback_data="generate_qr")
    keyboard.add(qr_button)
    return keyboard

def success_finish_kb():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Возврат в основное меню",callback_data="back2mainmenu"))
    keyboard.add(InlineKeyboardButton("Сгенерировать ещё один",callback_data="generate_qr"))
    return keyboard






