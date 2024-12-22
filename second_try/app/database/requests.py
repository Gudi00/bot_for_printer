from sqlalchemy.future import select
from app.database.models import async_session, User

async def set_user(tg_id: int, username: str):
    async with async_session() as session:
        user = await session.execute(select(User).where(User.tg_id == tg_id))
        user = user.scalar_one_or_none()

        if not user:
            new_user = User(tg_id=tg_id, username=username)
            session.add(new_user)
            await session.commit()