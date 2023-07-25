import logging
from io import BytesIO
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
import yaml
import qrcode
from keyboards import start_kb,success_finish_kb



logging.basicConfig(level=logging.INFO)

with open("config.yaml","r") as f:
    config = yaml.safe_load(f) ### config это словарь где ключ это токен а значение это уникальный пароль

bot = Bot(token = config['token'], parse_mode = types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())



class QRCodeGeneration(StatesGroup):
    waiting_for_url = State()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    qr_button = InlineKeyboardButton("Сгенерировать QR-код", callback_data="generate_qr")
    keyboard.add(qr_button)
    await message.answer("Выберите действие:", reply_markup=start_kb())

@dp.callback_query_handler(text="generate_qr")
async def generate_qr_code(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Введите URL, для которого нужно сгенерировать QR-код:")
    await QRCodeGeneration.waiting_for_url.set()

@dp.message_handler(state=QRCodeGeneration.waiting_for_url)
async def process_url(message: types.Message, state: FSMContext):
    try:
        data = message.text.strip()
        if not data.startswith('http://') and not data.startswith('https://'):
            data = 'https://' + data  # Add the protocol if it's missing
        qr = qrcode.QRCode(
            version=1,
            box_size=20,
            border=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        # Create a temporary BytesIO buffer to send the image without saving it to disk
        image_buffer = BytesIO()
        img.save(image_buffer)
        image_buffer.seek(0) # Move the pointer to the beginning of the buffer
        await bot.send_photo(message.from_user.id, photo=image_buffer)
        # Send a confirmation message and offer two options with a custom keyboard

        await message.answer("QR-код сгенерирован успешно!\nВыберите действие:", reply_markup=success_finish_kb())
        # Finish the state
        await state.finish()
    except Exception as e:
        await message.answer(f"Не удалось сгенерировать ошибку!{e}\nВыберите действие", reply_markup=success_finish_kb())


@dp.message_handler(lambda message: message.text == "Сгенерировать ещё один раз")
async def ask_for_url(message: types.Message):
    await message.answer("Введите URL для генерации нового QR-кода:")
    await QRCodeGeneration.waiting_for_url.set()


if __name__ == '__main__':
   executor.start_polling(dp, skip_updates=True)