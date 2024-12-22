import os
from sqlalchemy import select, update, func
from database.models import async_session, Order, Price, User
import logging

async def save_order(user_id: int, username: str, file_name: str, num_pages: int, total_cost: float):
    try:
        async with async_session() as session:
            order = Order(
                user_id=user_id,
                username=username,
                file_name=file_name,
                num_pages=num_pages,
                total_cost=total_cost
            )
            session.add(order)
            await session.commit()
    except Exception as e:
        logging.error(f"Error saving order: {e}")

async def get_prices():
    try:
        async with async_session() as session:
            prices = await session.scalars(select(Price))
            return {price.name: price.value for price in prices}
    except Exception as e:
        logging.error(f"Error getting prices: {e}")
        return {}

async def save_user(user_data: dict):
    try:
        async with async_session() as session:
            user = User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name')
            )
            session.add(user)
            await session.commit()
    except Exception as e:
        logging.error(f"Error saving user: {e}")

async def get_orders_summary():
    async with async_session() as session:
        total_orders = await session.scalar(select(func.count(Order.id)))
        total_income = await session.scalar(select(func.sum(Order.total_cost)))
        return total_orders, total_income

async def get_user_orders_summary(user_id: int):
    async with async_session() as session:
        total_orders = await session.scalar(select(func.count(Order.id)).where(Order.user_id == user_id))
        total_income = await session.scalar(select(func.sum(Order.total_cost)).where(Order.user_id == user_id))
        return total_orders, total_income

async def set_discount(username: str, discount: float):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.username == username))
        if user:
            user.discount = discount
            await session.commit()

async def update_prices(prices: dict):
    async with async_session() as session:
        for name, value in prices.items():
            stmt = update(Price).where(Price.name == name).values(value=value)
            await session.execute(stmt)
        await session.commit()

def get_all_files():
    files = []
    for file_name in os.listdir('downloads'):
        files.append(os.path.join('downloads', file_name))
    return files

def clear_downloads():
    files = get_all_files()
    for file_path in files:
        os.remove(file_path)