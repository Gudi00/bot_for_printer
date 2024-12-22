from sqlalchemy import select, update, func
from database.models import async_session, Order, Price
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