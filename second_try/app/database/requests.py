from sqlalchemy.future import select
from app.database.models import async_session, User, Price

async def set_user(tg_id: int, username: str):
    async with async_session() as session:
        user = await session.execute(select(User).where(User.tg_id == tg_id))
        user = user.scalar_one_or_none()

        if not user:
            new_user = User(tg_id=tg_id, username=username)
            session.add(new_user)
            await session.commit()

async def get_prices():
    try:
        async with async_session() as session:
            prices = await session.scalars(select(Price))
            return {price.name: price.value for price in prices}
    except Exception as e:
        print('Error in take price')
        return {}