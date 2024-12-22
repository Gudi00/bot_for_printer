from sqlalchemy import select, update, func
from app.database.models import async_session, Order, Price

async def save_order(user_id, username, file_name, num_pages, total_cost):
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

async def get_prices():
    async with async_session() as session:
        prices = await session.scalars(select(Price))
        return {price.name: price.value for price in prices}

async def update_prices(prices):
    async with async_session() as session:
        for name, value in prices.items():
            stmt = update(Price).where(Price.name == name).values(value=value)
            await session.execute(stmt)
        await session.commit()

async def get_orders_summary():
    async with async_session() as session:
        total_orders = await session.scalar(select(func.count(Order.id)))
        total_income = await session.scalar(select(func.sum(Order.total_cost)))
        return total_orders, total_income

async def get_user_orders_summary(user_id):
    async with async_session() as session:
        total_orders = await session.scalar(select(func.count(Order.id)).where(Order.user_id == user_id))
        total_income = await session.scalar(select(func.sum(Order.total_cost)).where(Order.user_id == user_id))
        return total_orders, total_income

async def set_discount(username, discount):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.username == username))
        if user:
            user.discount = discount
            await session.commit()