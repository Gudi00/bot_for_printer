import os
import fitz  # PyMuPDF
from aiogram import Router, types
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import app.keyboards as kb
from app.config import load_config

router = Router()
config = load_config()

# Создаем директорию 'downloads', если она не существует
if not os.path.exists('downloads'):
    os.makedirs('downloads')

class OrderProcess(StatesGroup):
    waiting_for_pdf = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
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

        # Отправляем файл и данные администратору
        admin_chat_id = config['ADMIN_CHAT_ID']
        caption = f"Новый заказ от @{message.from_user.username} ({message.from_user.id})\nКоличество страниц: {num_pages}"
        await message.bot.send_document(chat_id=admin_chat_id, document=document.file_id, caption=caption)

        await message.answer("Ваш заказ был отправлен администратору. Спасибо!", reply_markup=kb.main)
        await state.clear()
    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке файла: {str(e)}")

async def process_invalid_pdf(message: Message):
    await message.answer("Пожалуйста, отправьте файл в формате PDF.")