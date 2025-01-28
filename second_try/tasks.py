from aiogram import Bot
from app.database.requests import update_number_of_orders_per_week, get_number_of_orders_per_week
from datetime import datetime, timedelta


async def send_streak_report(bot: Bot):
    print('_______________________')
    orders = await get_number_of_orders_per_week()
    for order in orders:
        # if order.discount == -1: У меня нет relationships с User где хранится реальная скидка
        update_number_of_orders_per_week(order.user_id, 1)
