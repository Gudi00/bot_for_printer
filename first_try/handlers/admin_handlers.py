from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Command
from app.database.requests import get_orders_summary, get_user_orders_summary, set_discount, update_prices, get_prices
from app.config import load_config

router = Router()
config = load_config()

@router.message(Command("update_prices"))
async def update_prices_command(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    args = message.get_args().split()
    if len(args) % 2 != 0:
        await message.answer("Использование: /update_prices <name> <value> [<name> <value> ...]")
        return

    prices = {args[i]: float(args[i+1]) for i in range(0, len(args), 2)}
    await update_prices(prices)
    await message.answer(f"Цены обновлены: {prices}")

@router.message(Command("get_prices"))
async def get_prices_command(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    prices = await get_prices()
    prices_text = "\n".join([f"{name}: {value}" for name, value in prices.items()])
    await message.answer(f"Актуальные цены:\n{prices_text}")

@router.message(Command("orders_summary"))
async def orders_summary(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    total_orders, total_income = await get_orders_summary()
    await message.answer(f"Общее количество заказов: {total_orders}\nОбщий доход: {total_income:.2f} копеек")

@router.message(Command("user_orders_summary"))
async def user_orders_summary(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    user_id = int(message.get_args())
    total_orders, total_income = await get_user_orders_summary(user_id)
    await message.answer(f"Количество заказов пользователя {user_id}: {total_orders}\nДоход от пользователя: {total_income:.2f} копеек")

@router.message(Command("set_discount"))
async def set_user_discount(message: Message):
    if message.from_user.id != int(config['ADMIN_CHAT_ID']):
        return

    args = message.get_args().split()
    if len(args) != 2:
        await message.answer("Использование: /set_discount <username> <discount>")
        return

    username, discount = args
    discount = float(discount)
    await set_discount(username, discount)
    await message.answer(f"Скидка {discount:.2f} установлена для пользователя {username}")