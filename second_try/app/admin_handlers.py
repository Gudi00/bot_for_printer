import os
from aiogram import Router, types, Bot, Dispatcher
from aiogram.types import Message, InputFile, CallbackQuery
from aiogram.filters import Command
from app.database.requests import (
    get_orders_summary, get_user_orders_summary, set_discount, update_order_status,
    update_prices, get_prices, get_all_files, clear_downloads, get_order_user_id, ban_user, unban_user
)
from app.config import load_config

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

    prices = await get_prices()
    prices_text = "\n".join([f"{name}: {value} рублей" for name, value in prices.items()])
    await message.answer(f"Актуальные цены:\n{prices_text}")

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
        await message.answer("Использование: /set_discount <username> <discount>")
        return

    username, discount = args[1], args[2]

    discount = float(discount)
    await set_discount(username, discount)
    await message.answer(f"Скидка {discount:.2f} установлена для пользователя {username}")

# @router.message(Command("get_all_files"))
# async def get_all_files_command(message: Message):
#     if message.from_user.id != int(config['ADMIN_CHAT_ID']):
#         return
#
#     files = get_all_files()
#     for filepath in files:
#         document_file = InputFile(filepath)
#         await message.answer_document(document_file)

@router.message(Command("clear_downloads"))
async def clear_downloads_command(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    clear_downloads()
    await message.answer("Папка 'downloads' очищена.")

@router.message()
async def handle_reaction(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return
    bot_user = await bot.get_me()
    if message.reply_to_message and message.reply_to_message.from_user.id == bot_user.id:
        order_id = int(message.text)  # Предполагаем, что ID заказа находится в тексте сообщения
        user_id = await get_order_user_id(order_id)
        if user_id:
            result = await update_order_status(order_id, 'completed')
            if result == 1:
                await message.bot.send_message(user_id,
                                               f"Ваш заказ #{order_id} готов к выдаче!\nЖдём вас в комнате 1204а")
                await message.answer(f"Заказ #{order_id} успешно подтверждён")
            elif result == 2:
                await message.answer(f"Заказ #{order_id} уже подтверждён")
            elif result == 0:
                await message.answer(f"Заказ #{order_id} был отменёт. Я не могу сделать его выполненым")






def register_admin_handlers(dp: Dispatcher):
    dp.include_router(router)