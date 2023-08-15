import logging
from io import BytesIO
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def get_confirmation_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    yes_button = KeyboardButton(text="Yes, all correct")
    try_again_button = KeyboardButton(text="Try entering again")
    return_keyboard = KeyboardButton(text="Return to main menu")
    keyboard.add(yes_button, try_again_button, return_keyboard)
    return keyboard
def choose_generation_options_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    use_references_button = KeyboardButton(text="Use ready references")
    custom_prompt_button = KeyboardButton(text="Try with my prompt")
    return_to_main_menu_button = KeyboardButton(text="Return to main menu")
    keyboard.add(use_references_button, custom_prompt_button, return_to_main_menu_button)
    return keyboard




