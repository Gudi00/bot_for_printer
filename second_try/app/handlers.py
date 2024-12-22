import os
import fitz  # PyMuPDF
from aiogram import Router, types, Bot, Dispatcher
from aiogram.types import Message, ContentType, InputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import app.keyboards as kb
from app.config import load_config
from app.database.requests import save_order, get_prices, save_user

router = Router()
config = load_config()

# Создаем директорию 'downloads', если она не существует
if not os.path.exists('downloads'):
    os.makedirs('downloads')

class OrderProcess(StatesGroup):
    waiting_for_pdf = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    # Сохраняем данные пользователя в базу данных
    await save_user(tg_id=message.from_user.id, username=message.from_user.username,
                    first_name=message.from_user.first_name, last_name=message.from_user.last_name)

    # Отправляем уведомление администратору
    admin_chat_id = config['ADMIN_CHAT_ID']
    await message.bot.send_message(admin_chat_id,
                                   f"Новый пользователь @{message.from_user.username} ({message.from_user.id}) начал использовать бота.")

    await message.answer("Нажмите кнопку 'Создать заказ' для начала оформления заказа.", reply_markup=kb.main)

@router.message(lambda message: message.text == 'Создать заказ')
async def create_order(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, отправьте PDF файл.")
    await state.set_state(OrderProcess.waiting_for_pdf)

@router.message(OrderProcess.waiting_for_pdf)
async def process_message(message: Message, state: FSMContext):
    if message.content_type == ContentType.DOCUMENT:
        await process_pdf(message, state)
    else:
        await process_invalid_pdf(message)

async def process_pdf(message: Message, state: FSMContext):
    document = message.document

    # Проверяем MIME-тип документа
    if document.mime_type != 'application/pdf':
        await message.answer("Пожалуйста, отправьте файл в формате PDF.")
        return

    file = await message.bot.get_file(document.file_id)
    file_path = file.file_path
    downloaded_file = await message.bot.download_file(file_path)

    try:
        # Сохраняем загруженный файл
        file_save_path = f"downloads/{document.file_name}"
        with open(file_save_path, 'wb') as f:
            f.write(downloaded_file.read())

        # Открываем PDF файл и получаем количество страниц
        pdf_document = fitz.open(file_save_path)
        num_pages = pdf_document.page_count

        # Получаем цены из базы данных
        prices = await get_prices()

        if num_pages == 1:
            total_cost = 0.30
        elif 2 <= num_pages <= 5:
            total_cost = num_pages * prices['my_paper_2_5']
        elif 6 <= num_pages <= 20:
            total_cost = num_pages * prices['my_paper_6_20']
        elif 21 <= num_pages:
            total_cost = num_pages * prices['my_paper_21_150']

        # Сохранение заказа в базе данных
        await save_order(
            user_id=message.from_user.id,
            username=message.from_user.username,
            file_name=document.file_name,
            num_pages=num_pages,
            total_cost=total_cost
        )

        # Отправляем файл и данные администратору
        admin_chat_id = config['ADMIN_CHAT_ID']
        caption = (f"Новый заказ от @{message.from_user.username} ({message.from_user.id})\n"
                   f"Количество страниц: {num_pages}\nСтоимость: {total_cost:.2f} рублей")
        await message.bot.send_document(chat_id=admin_chat_id, document=document.file_id, caption=caption)

        await message.answer(f"Ваш заказ был отправлен администратору.\nИтоговая стоимость: {total_cost:.2f} рублей\nСпасибо за заказ", reply_markup=kb.main)
        await state.clear()
    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке файла: {str(e)}")

async def process_invalid_pdf(message: Message):
    await message.answer("Пожалуйста, отправьте файл в формате PDF.")

def register_main_handlers(dp: Dispatcher):
    dp.include_router(router)