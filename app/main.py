import logging
from io import BytesIO
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
import qrcode
import os,torch
from aiogram.utils import markdown as md
from keyboards import start_kb,success_finish_kb
from sd_text2image import pipe
from handlers import show_help
from dotenv import load_dotenv

# Загрузите переменные окружения из файла .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
# Глобальные переменные для хранения URL и статуса подтверждения
user_url = None
confirmation_status = False
positive_prompt = None

logging.basicConfig(level=logging.INFO)

bot = Bot(token = TOKEN, parse_mode = types.ParseMode.HTML)
dp = Dispatcher(bot)

def get_confirmation_keyboard():
    # Создаем клавиатуру с кнопками "Да, всё верно" и "Попробовать еще раз ввести"
    keyboard = InlineKeyboardMarkup()
    yes_button = InlineKeyboardButton(text="Да, всё верно", callback_data="confirm_url")
    try_again_button = InlineKeyboardButton(text="Попробовать еще раз ввести", callback_data="try_again")
    keyboard.add(yes_button, try_again_button)
    return keyboard

def get_choice_keyboard():
    # Создаем клавиатуру с кнопками "Использовать готовые референсы" и "Попробовать со своим промптом"
    keyboard = InlineKeyboardMarkup()
    use_references_button = InlineKeyboardButton(text="Использовать готовые референсы", callback_data="use_references")
    custom_prompt_button = InlineKeyboardButton(text="Попробовать со своим промптом", callback_data="custom_prompt")
    keyboard.add(use_references_button, custom_prompt_button)
    return keyboard
def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        box_size=20,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_L
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    return img
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


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    # Создаем клавиатуру с кнопкой "Сгенерировать Qr-код"
    welcome_text = """
            <b>Available commands:</b>
            /start - Start the QR Code generation process.
            /help - Show help message.
            """
    await message.answer(welcome_text, parse_mode=types.ParseMode.HTML)
    keyboard = InlineKeyboardMarkup()
    generate_qr_button = InlineKeyboardButton(text="Сгенерировать Qr-код", callback_data="generate_qr")
    keyboard.add(generate_qr_button)

    # Отправляем сообщение с просьбой нажать на кнопку
    await message.answer("Привет! Нажми на кнопку, чтобы сгенерировать Qr-код.", reply_markup=keyboard)

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    formatted_message = await show_help(message)
    await message.answer(text=formatted_message, parse_mode=types.ParseMode.MARKDOWN)

# Обработчик нажатия на кнопку "Сгенерировать Qr-код"
@dp.callback_query_handler(lambda c: c.data == "generate_qr")
async def generate_qr_callback(callback_query: types.CallbackQuery):
    global confirmation_status
    # Отправляем сообщение, запрашивая у пользователя ввести URL
    await bot.send_message(callback_query.from_user.id, "Введите URL, для которого нужно сгенерировать Qr-код:")
    # Отвечаем на запрос обработчика для избежания исключения
    await callback_query.answer()

# Обработчик текстовых сообщений (для ввода пользователем промпта)
@dp.message_handler(lambda message: message.from_user.id == positive_prompt, content_types=types.ContentTypes.TEXT)
async def process_custom_prompt(message: types.Message):
    global positive_prompt
    if positive_prompt is not None:
        # Сохраняем введенный пользователем промпт в переменную positive_prompt
        positive_prompt = message.text
        await message.reply(f"Вы ввели свой промпт: {positive_prompt}")
        logging.info("start diffusion (∩ ͡° ͜ʖ ͡°)⊃━☆ﾟ. *")
        negative_prompt_value='bad,ugly,nsfw, worst quality'
        qr_code_img = generate_qr_code(user_url)  # Генерируем QR-код с user_url
        output_img = generate_command(qr_code_img.get_image(), positive_prompt, negative_prompt_value)
        await bot.send_photo(message.from_user.id, photo=output_img)
        positive_prompt = None  # Сбрасываем positive_prompt после сохранения
        await message.answer("QR-код сгенерирован успешно!\nВыберите действие:", reply_markup=success_finish_kb())

# Обработчик текстовых сообщений
@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def process_text_message(message: types.Message):
    global user_url, confirmation_status, positive_prompt
    if user_url is None:
        # Сохраняем введенный пользователем URL в переменную
        user_url = message.text
        await message.reply(f"Вы ввели URL: {user_url}. Убедитесь, что вы правильно ввели информацию, которую нужно "
                            f"закодировать.", reply_markup=get_confirmation_keyboard())
        confirmation_status = True
        positive_prompt = None  # Сбрасываем positive_prompt после ввода URL
    else:
        if positive_prompt is not None:
            # Если positive_prompt не равно None, значит, пользователь только что ввел свой промпт
            # и мы его обработали, поэтому пропускаем эту часть и не отправляем в меню снова.

            return
        await message.reply("Вы уже ввели URL. Чтобы сгенерировать новый Qr-код, используйте команду /start.")

# Обработчик нажатия на кнопки подтверждения
@dp.callback_query_handler(lambda c: c.data in ["confirm_url", "try_again"])
async def confirmation_callback(callback_query: types.CallbackQuery):
    global user_url, confirmation_status
    if callback_query.data == "confirm_url":
        # Здесь вы можете добавить код для генерации Qr-кода из переменной user_url
        user_url = None  # Сбрасываем URL после подтверждения
        confirmation_status = False
        await bot.send_message(callback_query.from_user.id, "Вы можете выбрать одну из опций:", reply_markup=get_choice_keyboard())
        await callback_query.answer()
    elif callback_query.data == "try_again":
        user_url = None  # Сбрасываем URL, чтобы пользователь мог ввести его снова
        await bot.send_message(callback_query.from_user.id, "Введите URL, для которого нужно сгенерировать Qr-код:")
        await callback_query.answer()

# Обработчик нажатия на кнопки выбора
@dp.callback_query_handler(lambda c: c.data in ["use_references", "custom_prompt"])
async def choice_callback(callback_query: types.CallbackQuery):
    global positive_prompt
    if callback_query.data == "use_references":
        await callback_query.answer("Выбрана опция 'Использовать готовые референсы'")
        positive_prompt = None

    elif callback_query.data == "custom_prompt":
        await callback_query.answer("Выбрана опция 'Попробовать со своим промптом'")
        await bot.send_message(callback_query.from_user.id, "Введите свой промпт:")
        positive_prompt = callback_query.from_user.id  # Сохраняем ID пользователя для связывания с промптом
         # Отвечаем на запрос обработчика для избежания исключения
    await callback_query.answer()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
