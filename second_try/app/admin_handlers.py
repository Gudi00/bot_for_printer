import os
from aiogram import Router, types, Bot, Dispatcher
from aiogram.types import Message, InputFile, CallbackQuery
from aiogram.filters import Command
from aiogram.types import FSInputFile

from app.database.requests import (
    get_orders_summary, get_user_orders_summary, set_discount, update_order_status,
    update_prices, get_prices_for_command, get_all_files, clear_downloads, get_order_user_id, ban_user, unban_user,
    generate_discount_message_admin, generate_discount_message_user, get_discount, getNoneOrders, update_money,
    update_number_of_messages, update_number_of_messages_from_last_order, get_messages_from_last_order, get_id_all_users,
    update_number_of_completed_orders,
)
from app.config import load_config
from io import BytesIO

router = Router()
config = load_config()
bot = Bot(token=config['BOT_TOKEN'])

@router.message(Command("ban"))
async def ban_command(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("Использование: /ban <user_id>")
        return

    try:
        user_id = int(args[1])
        await ban_user(user_id)
        await message.answer(f"Пользователь {user_id} забанен.")
    except Exception as e:
        await message.answer(f"Ошибка при бане пользователя: {e}")

# Обработчик команды для разбанивания пользователя
@router.message(Command("unban"))
async def unban_command(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("Использование: /unban <user_id>")
        return

    try:
        user_id = int(args[1])
        await unban_user(user_id)
        await message.answer(f"Пользователь {user_id} разбанен.")
        caption = (f"Прошу прошения, вы были заблокированы по ошибке😣 В качестве извинения предоставлем вам 5.00 рублей на следующие заказы")
        await update_money(user_id, 5)
        await message.bot.send_message(chat_id=user_id, text=caption)
    except Exception as e:
        await message.answer(f"Ошибка при разбане пользователя: {e}")

@router.message(Command("update_prices"))
async def update_prices_command(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    args = message.text.split()
    if len(args) % 2 == 0:
        await message.answer("Использование: /update_prices <name> <value> [<name> <value> ...]")
        return

    prices = {args[i]: float(args[i+1]) for i in range(1, len(args), 2)}
    await update_prices(prices)
    await message.answer(f"Цены обновлены: {prices}")

@router.message(Command("get_prices"))
async def get_prices_command(message: Message):
    prices = await get_prices_for_command()
    if message.from_user.id == int(config['ADMIN_CHAT_ID']):
        prices_text = await generate_discount_message_admin(prices)
    else:
        prices_text = await generate_discount_message_user(prices, await get_discount(message.from_user.id))
    await message.answer(f"{prices_text}")

@router.message(Command("orders_summary"))
async def orders_summary(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    total_orders, total_income = await get_orders_summary()
    await message.answer(f"Общее количество заказов: {total_orders}\nОбщий доход: {total_income:.2f} рублей")


@router.message(Command("user_orders_summary"))
async def user_orders_summary(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    user_id = int(message.text.split()[1])
    total_orders, total_income = await get_user_orders_summary(user_id)
    await message.answer(f"Количество заказов пользователя {user_id}: {total_orders}\nДоход от пользователя: {total_income:.2f} копеек")

@router.message(Command("set_discount"))
async def set_user_discount(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    args = message.text.split()
    if len(args) != 3:
        await message.answer("Использование: /set_discount <user_id> <discount>")
        return

    user_id, discount = int(args[1]), args[2]

    discount = float(discount)
    if await set_discount(user_id, discount):
        await message.answer(f"Скидка {discount:.2f} установлена для пользователя {user_id}")
    else:
        await message.answer(f"Ошибка в обновлении значения скидки")

# @router.message(Command("get_all_files"))
# async def get_all_files_command(message: Message):
#     if message.from_user.id != int(config['ADMIN_CHAT_ID']):
#         return
#
#     files = get_all_files()
#     for filepath in files:
#         document_file = InputFile(filepath)
#         await message.answer_document(document_file)

@router.message(Command("update_money"))
async def handle_update_money_command(message: types.Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return
    try:
        # Парсинг команды /update_money user_id new_money_value
        command_args = message.text.split()
        if len(command_args) != 3:
            await message.reply("Используйте команду в формате: /update_money <username> <new_money_value>")
            return

        user_id = int(command_args[1])
        new_money_value = float(command_args[2])

        # Обновление значения money
        await update_money(user_id, new_money_value)
        await message.reply(f"Значение money для пользователя с user_id {user_id} обновлено на {new_money_value}")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")

@router.message(Command("clear_downloads"))
async def clear_downloads_command(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    clear_downloads()
    await message.answer("Папка 'downloads' очищена.")

@router.message(Command("need_to_confirm"))
async def NoneOrders(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return
    await message.answer(f"{await getNoneOrders()}")

@router.message(Command("send_message_for_all_users"))
async def send_message_for_all_users(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    text = message.text.split()
    if len(text) != 2:
        await message.reply("Используйте команду в формате: /send_message_for_all_users <text>")
        return
    textForUsers = text[1]
    users = await get_id_all_users()
    for user in users:
        await message.bot.send_message(user.tg_id, textForUsers)
    await message.reply("Готово))")

@router.message()
async def handle_reaction(message: Message):

    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        await update_number_of_messages(message.from_user.id)
        await update_number_of_messages_from_last_order(message.from_user.id)

        if await get_messages_from_last_order(message.from_user.id) % 3 == 2:
            caption = ('Чтобы создать заказ, нужно нажать на кнопку "Создать заказ" внизу экрана. '
                'Иногда эта кнопка сворачивается и выглядит как квадрат с 4 точками рядом с кнопкой "Отправить сообщение". '
               '\n\n'
                'Если захотите узнать все возможности бота, то напишите /help')
            photo = FSInputFile("photo1.jpg")

            await message.answer_photo(photo=photo, caption=caption)

        return

    bot_user = await bot.get_me()
    if message.reply_to_message and message.reply_to_message.from_user.id == bot_user.id:
        text = message.text.split()
        order_id = int(text[0])  # Предполагаем, что ID заказа находится в тексте сообщения
        user_id = await get_order_user_id(order_id)
        if user_id:
            result = await update_order_status(order_id, 'completed')
            if len(text) > 1:
                await message.answer(f"Тихое подтверждение))\nЗаказ #{order_id} успешно подтверждён")
                await update_number_of_completed_orders(user_id)
            else:
                if result == 1:
                    await message.bot.send_message(user_id,
                                                   f"Ваш заказ #{order_id} готов к выдаче!\nЖдём вас в комнате 1204а")
                    await message.answer(f"Заказ #{order_id} успешно подтверждён")
                    await update_number_of_completed_orders(user_id)
                elif result == 2:
                    await message.answer(f"Заказ #{order_id} уже подтверждён")
                elif result == 0:
                    await message.answer(f"Заказ #{order_id} был отменёт. Я не могу сделать его выполненым")
                    await update_number_of_completed_orders(user_id)






def register_admin_handlers(dp: Dispatcher):
    dp.include_router(router)