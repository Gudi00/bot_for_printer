import os
from math import floor

import fitz  # PyMuPDF
from aiogram import Router, types, Bot, Dispatcher, F
from aiogram.types import Message, ContentType, InputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import app.keyboards as kb
from app.config import load_config
from app.database.requests import (save_order, get_prices, save_user, is_user_banned, get_discount,
                                   get_last_order_id, get_order_user_id, update_order_status, get_number_of_orders,
                                   update_number_of_orders, clear_downloads, update_money, damp_messages_from_last_order,
                                   ban_user, get_number_of_completed_orders, fetch_user_money, get_number_of_orders_per_week,
                                   update_number_of_orders_per_week, get_last_order_number, update_referral, get_ref)

router = Router()
config = load_config()

# Создаем директорию 'downloads', если она не существует
if not os.path.exists('downloads'):
    os.makedirs('downloads')

async def check_ban(message: Message):
    return await is_user_banned(message.from_user.id)

class OrderProcess(StatesGroup):
    waiting_for_pdf = State()



@router.message(Command("start"))
async def cmd_start(message: Message):
    # Сохраняем данные пользователя в базу данных
    if await save_user(tg_id=message.from_user.id, username=message.from_user.username,
                    first_name=message.from_user.first_name, last_name=message.from_user.last_name):

        # Отправляем уведомление администратору
        admin_chat_id = config['ADMIN_CHAT_ID']
        await message.bot.send_message(admin_chat_id,
                                       f"Новый пользователь @{message.from_user.username} ({message.from_user.id}) начал использовать бота.")
    if await check_ban(message):
        await message.answer(
            "Администратор вас заблакировал. Вполне возможно, что это ошибка.\nНапишите администратору, он вам обязательно поможет")

        return
    await message.answer("Нажмите кнопку 'Создать заказ' для начала оформления заказа или введите команду "
                         "/help, чтобы узнать все возможности бота", reply_markup=kb.main)



@router.message(lambda message: message.text == 'Создать заказ')
async def create_order(message: Message, state: FSMContext):
    if await check_ban(message):
        await message.answer(
            "Администратор вас заблакировал. Вполне возможно, что это ошибка.\nНапишите администратору, он вам обязательно поможет")
        await state.clear()
        return
    await cmd_start(message)
    if await get_number_of_orders(message.from_user.id) - await get_number_of_completed_orders(message.from_user.id) > 20:
        await ban_user(message.from_user.id)
        admin_chat_id = config['ADMIN_CHAT_ID']
        caption = (f"Пользователь был заблокирован за большое количество неподтверждённых заказов"
                   f"\n\nusername: {message.from_user.username}\n tg_id: {message.from_user.id}")
        await message.bot.send_message(chat_id=admin_chat_id, text=caption)


    await message.answer("Пожалуйста, отправьте PDF файл.")
    await state.set_state(OrderProcess.waiting_for_pdf)
    clear_downloads()

@router.message(OrderProcess.waiting_for_pdf)
async def process_message(message: Message, state: FSMContext):
    if await check_ban(message):
        await message.answer(
            "Администратор вас заблакировал. Вполне возможно, что это ошибка.\nНапишите администратору, он вам обязательно поможет")

        return
    await cmd_start(message)
    if message.content_type == ContentType.DOCUMENT:
        await process_pdf(message, state)
    else:
        await process_invalid_pdf(message)

async def process_pdf(message: Message, state: FSMContext):
    if await check_ban(message):
        return

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

        if num_pages > 300:
            await message.answer(f"В файле слишком много страниц. Отправьте его по отдельности (не более 300 страниц)")
            await state.clear()
            return

        # Получаем цены из базы данных
        prices = await get_prices()
        discount = float(await get_discount(message.from_user.id))
#дать высокую скидку для постоянных клиентов на ограниченое количество заказов
        # (проверка на наличие денег для новый неподтверждённых польхоавтелей, проверка на бесплатные листы)
        total_cost = 0
        number_of_orders = await get_number_of_orders(message.from_user.id)
        if discount == -1:
            discount = 0.2
            if num_pages < 6 and await get_number_of_orders_per_week(message.from_user.id) > 0:
                total_cost = 0.00
                await update_number_of_orders_per_week(message.from_user.id)

            #добавить счётчик, чтобы не абузили
        else:
            if number_of_orders > 6:
                discount = 0.5 * (1-number_of_orders*0.2)
            if num_pages == 1:
                total_cost = prices['my_paper_1'] * (1-discount)
            elif 2 <= num_pages <= 5:
                total_cost = num_pages * prices['my_paper_2_5'] * (1-discount)
            elif 6 <= num_pages <= 20:
                total_cost = num_pages * prices['my_paper_6_20'] * (1-discount)
            elif 21 <= num_pages:
                total_cost = num_pages * prices['my_paper_21_150'] * (1-discount)


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
        order_id = await get_last_order_id()

        cost = await update_money(message.from_user.id, -total_cost)
        await update_money(await get_ref(message.from_user.id) ,total_cost*0.1)
        send = ''
        if 7+order_id*0.7 <= total_cost or total_cost > 30:
             send = (f'У вас достаточно дорогой заказ, поэтому напишите лично @misha_iosko'
                       ' или зайдите к нему в блок, когда вам придёт уведомление')

        caption = (f"{send}\n#{order_id}\n\nНовый заказ от @{message.from_user.username} {message.from_user.id}\n"
                   f"Количество страниц: {num_pages}\nСкидка: {discount*100}% ({round(total_cost/(1-discount)*discount, 2)} рублей)"
                          f"\n\n{cost}")
        await message.bot.send_document(chat_id=admin_chat_id, document=document.file_id, caption=caption)


        caption = (f"{send}\n\nЗаказ номер {order_id}\n\n{cost}\n"
                   f"\nСкидка: {round(total_cost/(1-discount)*discount, 2)} рублей"
                   f"\n\nКогда заказ будет готов, вам придет сообщение в этот чат")
        await message.bot.send_document(chat_id=message.from_user.id, document=document.file_id, caption=caption, reply_markup=kb.main)
        await update_number_of_orders(message.from_user.id)
        await damp_messages_from_last_order(message.from_user.id)
        await state.clear()

    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке файла: {str(e)}")

@router.message(Command("money"))
async def send_fetch_user_money(message: Message):
    if await check_ban(message):
        await message.answer("Вы забанены и не можете выполнять эту команду.")
        return
    await cmd_start(message)
    money = await fetch_user_money(message.from_user.id)
    await message.answer(f"У вас на счету {money} рублей")
@router.message(Command("help"))
async def help_command(message: Message):

    await message.answer("Этот бот нужет для экономия вашего времени;) Но он принимает только PDF файлы((\n\nБот может:"
                         "\n1. Принимать заказы при нажатие на кнопку 'Создать заказ'."
                         "\n2. Отправлять сообщение, когда администатор выполнит ваш заказ."
                         "\n\nПолезные команды для работы с ботом:"
                         "\n/cancel_order {number} - отменяет заказ под номером number"
                         "\n/get_prices - отправит вам актуальные цены на печать")
    await cmd_start(message)




@router.message(Command("cancel_order"))
async def cancel_order_command(message: Message):
    if await check_ban(message):
        await message.answer("Вы забанены и не можете выполнять эту команду.")
        return
    await cmd_start(message)
    args = message.text.split()
    if len(args) != 2:
        await message.answer("Использование: /cancel_order номер_заказа")
        return

    try:
        order_id = int(args[1])
        user_id = await get_order_user_id(order_id)
        if user_id == message.from_user.id or message.from_user.id == int(config['ADMIN_CHAT_ID']):#добавил отмену через админа
            result = await update_order_status(order_id, 'cancelled')
            if result == 1:
                await message.answer(f"Ваш заказ #{order_id} успешно отменён.")
                await message.bot.send_message(config['ADMIN_CHAT_ID'], f"Заказ #{order_id} отменён пользователем @{message.from_user.username}.")
            elif result == 2:
                await message.answer(f"Заказ #{order_id} уже отменён.")
            elif result == 0:
                await message.answer(f"Заказ с идентификатором #{order_id} уже выполнен, поэтому вы не можете его отменить")
        else:
            await message.answer("Вы не можете отменить этот заказ, так как он сделан другим пользователем.")
    except ValueError:
        await message.answer("Неверный формат номера заказа.")
    except Exception as e:
        await message.answer(f"Ошибка при отмене заказа: {e}")

async def process_invalid_pdf(message: Message):
    if await check_ban(message):
        return
    await message.answer("Пожалуйста, отправьте файл в формате PDF.")





class for_me(StatesGroup):
    user_message = State()

@router.message(F.text == 'Комментарий к заказу')
async def start_saving_for_creator(message: Message, state: FSMContext):
    await cmd_start(message)
    await message.answer("Теперь вы можете отпавить комментарий к заказу. Если это не обычный запрос, то итоговая цена может измениться", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(for_me.user_message)

@router.message(Command("message_for_creator"))
async def start_saving_for_creator(message: Message, state: FSMContext):
    await cmd_start(message)
    await message.answer("Теперь вы можете отпавить сообщение для разработчика", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(for_me.user_message)

@router.message(for_me.user_message)
async def send_for_creator(message: Message, state: FSMContext):
    await cmd_start(message)
    await message.bot.send_message(config['ADMIN_CHAT_ID'],
                                   f"К заказу номер {await get_last_order_number(message.from_user.id)}"
                                   f"\n@{message.from_user.username} советует:\n\n{message.text}")
    await state.clear()
    await message.answer('Ваше сообщение отправлено', reply_markup=kb.main)

@router.message(Command("update_referral"))
async def update_ref(message: Message):
    await cmd_start(message)
    args = message.text.split()
    if len(args) != 2:
        await message.answer("Использование: /update_referral <username>")
        return
    discount, ref_id = await update_referral(args[1], message.from_user.id)
    if ref_id and discount:
        await message.answer(f"Всё получилось, типерь ваша скидка увеличилась до {discount*100}%")
        await message.bot.send_message(chat_id=ref_id,
                                       text=f"@{message.from_user.username} перешёл по вашей реферальной ссылке, "
                                            f"теперь вы будете получать 10% со всех его заказов")
    elif ref_id == 0 and discount == 0:
        await message.answer(f"Этот пользователь никогда не пользовался новой версией бота. "
                             f"Попросите его написать в чат команду '/start' или перепроверьте правильность написания")
    else:
        await message.answer(f"Вы уже переходили по реферальным ссылкам")



def register_main_handlers(dp: Dispatcher):
    dp.include_router(router)