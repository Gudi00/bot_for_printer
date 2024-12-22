import os
import fitz  # PyMuPDF
from aiogram import Router, types
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import app.keyboards as kb
from app.config import load_config

from first_try.app.database.requests import get_prices, save_order

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

        # Получаем цены из базы данных
        prices = await get_prices()

        if num_pages == 1:
            total_cost = 0.50
        elif 2 <= num_pages <= 5:
            total_cost = num_pages * prices['my_paper_2_5']
        elif 6 <= num_pages <= 20:
            total_cost = num_pages * prices['my_paper_6_20']
        elif 21 <= num_pages <= 150:
            total_cost = num_pages * prices['my_paper_21_150']
        else:
            total_cost = 0  # Handle case for more than 150 pages if needed

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
        caption = (f"Новый заказ от @{message.from_user.username} ({message.from_user.id})\nКоличество страниц: "
                   f"{num_pages}\nСтоимость: {total_cost:.2f} копеек")
        await message.bot.send_document(chat_id=admin_chat_id, document=document.file_id, caption=caption)

        # # Отправляем файл и данные администратору
        # admin_chat_id = config['ADMIN_CHAT_ID']
        # caption = f"Новый заказ от @{message.from_user.username} ({message.from_user.id})\nКоличество страниц: {num_pages}"
        # await message.bot.send_document(chat_id=admin_chat_id, document=document.file_id, caption=caption)

        await message.answer("Ваш заказ был отправлен администратору. Спасибо!", reply_markup=kb.main)
        await state.clear()
    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке файла: {str(e)}")

async def process_invalid_pdf(message: Message):
    await message.answer("Пожалуйста, отправьте файл в формате PDF.")
# import os
# import fitz  # PyMuPDF
# from aiogram import Router, types
# from aiogram.types import Message, ContentType, InputFile
# from aiogram.filters import Command
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup
#
# import app.keyboards as kb
# from app.config import load_config
# from app.database.requests import save_order, get_prices
#
# router = Router()
# config = load_config()
#
# # Создаем директорию 'downloads', если она не существует
# if not os.path.exists('downloads'):
#     os.makedirs('downloads')
#
#
# # Определяем состояния для FSM
# class OrderProcess(StatesGroup):
#     waiting_for_pdf = State()
#
#
# @router.message(Command("start"))
# async def cmd_start(message: Message, state: FSMContext):
#     await message.answer("Нажмите кнопку 'Создать заказ' для начала оформления заказа.", reply_markup=kb.main)
#
#
# @router.message(lambda message: message.text == 'Создать заказ')
# async def create_order(message: Message, state: FSMContext):
#     await message.answer("Пожалуйста, отправьте PDF файл.")
#     await state.set_state(OrderProcess.waiting_for_pdf)
#
#
# @router.message(OrderProcess.waiting_for_pdf)
# async def process_pdf(message: Message, state: FSMContext):
#     if message.content_type != ContentType.DOCUMENT or message.document.mime_type != 'application/pdf':
#         await message.answer("Пожалуйста, отправьте файл в формате PDF.")
#         return
#
#     document = message.document
#     file = await message.bot.get_file(document.file_id)
#     file_path = file.file_path
#     downloaded_file = await message.bot.download_file(file_path)
#
#     try:
#         # Сохраняем загруженный файл
#         file_save_path = f"downloads/{document.file_name}"
#         with open(file_save_path, 'wb') as f:
#             f.write(downloaded_file.read())
#
#         # Открываем PDF файл и получаем количество страниц
#         pdf_document = fitz.open(file_save_path)
#         num_pages = pdf_document.page_count
#
#         # Получаем цены из базы данных
#         prices = await get_prices()
#
#         if num_pages == 1:
#             total_cost = 0.50
#         elif 2 <= num_pages <= 5:
#             total_cost = num_pages * prices['my_paper_2_5']
#         elif 6 <= num_pages <= 20:
#             total_cost = num_pages * prices['my_paper_6_20']
#         elif 21 <= num_pages <= 150:
#             total_cost = num_pages * prices['my_paper_21_150']
#         else:
#             total_cost = 0  # Handle case for more than 150 pages if needed
#
#         # Сохранение заказа в базе данных
#         await save_order(
#             user_id=message.from_user.id,
#             username=message.from_user.username,
#             file_name=document.file_name,
#             num_pages=num_pages,
#             total_cost=total_cost
#         )
#
#         # Отправляем файл и данные администратору
#         admin_chat_id = config['ADMIN_CHAT_ID']
#         caption = f"Новый заказ от @{message.from_user.username} ({message.from_user.id})\nКоличество страниц: {num_pages}\nСтоимость: {total_cost:.2f} копеек"
#
#         document_file = InputFile(file_save_path)
#         await message.bot.send_document(chat_id=admin_chat_id, document=document_file, caption=caption)
#
#         await message.answer("Ваш заказ был отправлен администратору. Спасибо!", reply_markup=kb.main)
#         await state.clear()
#     except Exception as e:
#         await message.answer(f"Произошла ошибка при обработке файла: {str(e)}")
#
#
# async def process_invalid_pdf(message: Message):
#     await message.answer("Пожалуйста, отправьте файл в формате PDF.")