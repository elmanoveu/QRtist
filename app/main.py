import logging
from io import BytesIO
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import qrcode
from sd_text2image import pipe
import os,torch
from handlers import show_help
from dotenv import load_dotenv
from keyboards import choose_generation_options_keyboard,get_confirmation_keyboard

# Загрузите переменные окружения из файла .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

text2generate=None
logging.basicConfig(level=logging.INFO)

bot = Bot(token = TOKEN, parse_mode = types.ParseMode.HTML)
dp = Dispatcher(bot)



def generate_command(source_image, prompt_value, negative_prompt_value, controlnet_conditioning_scale_value=1.8):
    generator = torch.manual_seed(123121231)
    # Ваш код для работы с pipe и получения результата
    image = pipe(prompt=prompt_value,
                 negative_prompt=negative_prompt_value,
                 image=source_image, width=768,
                 height=768,
                 guidance_scale=25,
                 controlnet_conditioning_scale=1.8,
                 generator=generator, num_inference_steps=50)
    final_img = image.images[0]
    logging.info(f"{type(final_img)}")
    image_format = 'JPEG'
    image_buffer = BytesIO()
    final_img.save(image_buffer, format=image_format)
    image_buffer.seek(0)  # Move the pointer to the beginning of the buffer
    return image_buffer
def generate_qr_code(url_or_text):
    qr = qrcode.QRCode(
        version=1,box_size=20,
        border=4,error_correction=qrcode.constants.ERROR_CORRECT_L
    )
    qr.add_data(url_or_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    return img

class QRCodeGenerationStates(StatesGroup):
    waiting_for_text = State()   # Состояние ожидания ввода текста для QR-кода
    waiting_for_prompt = State()  # Состояние ожидания ввода пользовательского текста

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    # Создаем клавиатуру с кнопкой "Сгенерировать Qr-код"
    welcome_text = """
            <b>Available commands:</b>
            /start - Start the QR Code generation process.
            /help - Show help message.
            """
    await message.answer(welcome_text, parse_mode=types.ParseMode.HTML)
    generate_qr_button = KeyboardButton(text="Сгенерировать Qr-код")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(generate_qr_button)
    await message.answer("Привет! Нажми на кнопку, чтобы сгенерировать Qr-код.", reply_markup=keyboard)
@dp.message_handler(lambda message: message.text == "Сгенерировать Qr-код")
async def generate_qr_button_handler(message: types.Message):
    global text2generate
    await message.answer("Введите текст для генерации QR-кода.")
    # Устанавливаем состояние ожидания ввода текста
    text2generate = message.text
    await QRCodeGenerationStates.waiting_for_text.set()
@dp.message_handler(state=QRCodeGenerationStates.waiting_for_text)
async def process_generated_text(message: types.Message, state: FSMContext):
    user_input_text = message.text
    await state.finish()  # Завершаем состояние ожидания ввода текста
    confirmation_keyboard = get_confirmation_keyboard()
    await message.answer(f"Вы ввели: {user_input_text}\nПодтверждаете правильность?",
                         reply_markup=confirmation_keyboard)
    await state.update_data(user_input_text=user_input_text)

@dp.message_handler(lambda message: message.text == "Try entering again")
async def try_entering_again_handler(message: types.Message):
    await message.answer("Please enter the text for QR code generation.")
    await QRCodeGenerationStates.waiting_for_text.set()

@dp.message_handler(lambda message: message.text in ["Yes, all correct"])
async def confirm_text_handler(message: types.Message):
    await message.answer("Great! Now you have the following options:")
    choice_keyboard = choose_generation_options_keyboard()
    await message.answer("What would you like to do?", reply_markup=choice_keyboard)

@dp.message_handler(lambda message: message.text == "Try with my prompt")
async def try_with_prompt_handler(message: types.Message):
    await message.answer("Please enter your custom prompt:")
    await QRCodeGenerationStates.waiting_for_prompt.set()  # Создаем состояние ожидания ввода пользовательского текста

@dp.message_handler(lambda message: message.text == "Return to main menu")
async def return_to_main_menu_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await start_command(message)  # Вызываем обработчик команды /start

@dp.message_handler(state=QRCodeGenerationStates.waiting_for_prompt)
async def process_custom_prompt(message: types.Message, state: FSMContext):
    global text2generate
    positive_prompt = message.text
    await state.finish()  # Завершаем состояние ожидания ввода пользовательского текста
    # Сохраняем введенный пользовательский текст в переменную positive_prompt
    await state.update_data(positive_prompt=positive_prompt)
    await message.reply(f"Вы ввели свой промпт: {positive_prompt}")
    logging.info("start diffusion (∩ ͡° ͜ʖ ͡°)⊃━☆ﾟ. *")
    negative_prompt_value = 'bad,ugly,nsfw, worst quality'
    qr_code_img = generate_qr_code(text2generate)  # Генерируем QR-код с user_url
    output_img = generate_command(qr_code_img.get_image(), positive_prompt, negative_prompt_value)
    await bot.send_photo(message.from_user.id, photo=output_img)
    positive_prompt = None  # Сбрасываем positive_prompt после сохранения
    text2generate = None
    await message.answer("QR-код сгенерирован успешно!\n Попробуете еще раз?" , reply_markup=choose_generation_options_keyboard())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
