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
import torch
from aiogram.utils import markdown as md
from keyboards import start_kb,success_finish_kb
from sd_text2image import pipe


logging.basicConfig(level=logging.INFO)

with open("config.yaml","r") as f:
    config = yaml.safe_load(f) ### config это словарь где ключ это токен а значение это уникальный пароль

bot = Bot(token = config['token'], parse_mode = types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())



class QRCodeGeneration(StatesGroup):
    waiting_for_url = State()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    welcome_text = """
        <b>Available commands:</b>
        /start - Start the QR Code generation process.
        /help - Show help message.
        """
    await message.answer(welcome_text, parse_mode=types.ParseMode.HTML)
    keyboard = InlineKeyboardMarkup()
    qr_button = InlineKeyboardButton("Сгенерировать QR-код", callback_data="generate_qr")
    keyboard.add(qr_button)
    await message.answer("Выберите действие:", reply_markup=start_kb())

@dp.message_handler(commands=['help'])
async def show_help(message: types.Message):
    message_text = "Появление QR-кода - это один из наиболее удобных и многообещающих инноваций в мире технологий. " \
                   "Эти квадратные матричные коды представляют собой уникальную комбинацию черных и белых " \
                   "квадратов, способных хранить разнообразную информацию. Вот несколько ключевых возможностей " \
                   "QR-кода, которые делают его таким удобным и популярным:\n\n"

    formatted_message = md.text(message_text,
        md.bold("Быстрый доступ к информации:"), "QR-коды позволяют быстро получать доступ к различным видам "
                                                 "информации. Пользователи могут легко сканировать коды с помощью "
                                                 "камеры своего смартфона или планшета, что позволяет получать текстовую "
                                                 "информацию, URL-ссылки, контактные данные, географические координаты и "
                                                 "многое другое. Это делает процесс передачи и получения данных более "
                                                 "удобным и эффективным.\n\n",
        md.bold("Продвижение бренда и продукции:"), "QR-коды стали мощным инструментом для маркетинговых кампаний. "
                                                    "Они могут быть использованы для привлечения внимания к брендам и "
                                                    "продукции, а также для предоставления потенциальным клиентам скидок, "
                                                    "акций и специальных предложений. Размещение QR-кода на упаковке "
                                                    "товара, в рекламных материалах или на витринах магазинов помогает "
                                                    "привлечь новых клиентов и укрепить лояльность существующих.\n\n",
        md.bold("Упрощение оплаты и авторизации:"), "QR-коды активно применяются в сфере финансовых технологий. Они "
                                                    "позволяют клиентам совершать быстрые и безопасные платежи через "
                                                    "мобильные приложения или мобильные кошельки. Кроме того, QR-коды могут "
                                                    "быть использованы для авторизации пользователей, аутентификации и "
                                                    "получения доступа к различным онлайн-сервисам. Благодаря этим "
                                                    "возможностям, QR-коды играют ключевую роль в развитии цифровой "
                                                    "экономики и улучшении пользовательского опыта.\n\n",
        "В целом, QR-коды представляют собой универсальный инструмент с широким спектром применения: от личного "
        "использования для быстрого доступа к информации до коммерческих задач, таких как маркетинг и оплата. Их "
        "удобство, эффективность и простота использования делают QR-коды незаменимым элементом в современном цифровом "
        "мире."
    )

    await message.answer(text=formatted_message, parse_mode=types.ParseMode.MARKDOWN)

@dp.callback_query_handler(text="generate_qr")
async def generate_qr_code(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Введите URL, для которого нужно сгенерировать QR-код:")
    await QRCodeGeneration.waiting_for_url.set()

async def generate_command(source_image, prompt_value, negative_prompt_value,
                        controlnet_conditioning_scale_value=1.8):

        generator = torch.manual_seed(123121231)
        # Ваш код для работы с pipe и получения результата
        image = pipe(prompt=prompt_value, negative_prompt=negative_prompt_value,
                     image=source_image, width=768, height=768, guidance_scale=25,
                     controlnet_conditioning_scale=controlnet_conditioning_scale_value,
                     generator=generator, num_inference_steps=50)

        return image


@dp.message_handler(state=QRCodeGeneration.waiting_for_url)
async def process_url(message: types.Message, state: FSMContext):
    try:
        data = message.text.strip()
        if not data.startswith('http://') and not data.startswith('https://'):
            data = 'https://' + data  # Add the protocol if it's missing
        qr = qrcode.QRCode(
            version=1,
            box_size=20,
            border=4,
            error_correction=qrcode.constants.ERROR_CORRECT_L
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        # Create a temporary BytesIO buffer to send the image without saving it to disk
        make_diffusion=True
        if not make_diffusion:
            image_buffer = BytesIO()
            img.save(image_buffer)
            image_buffer.seek(0) # Move the pointer to the beginning of the buffer
            await bot.send_photo(message.from_user.id, photo=image_buffer)
            # Send a confirmation message and offer two options with a custom keyboard
        else:
            prompt_value = "(masterpiece, top quality, best quality, extreme detailed, highest detailed, official art, beautiful and aesthetic:1.2), colorful, cowboy shot, beautiful face, solo",
            negative_prompt_value = " (worst quality:2), (low quality:2), (normal quality:2),",
            generate_command(img.get_image(),prompt_value,negative_prompt_value)

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