from sqlalchemy import select, update, func
from app.database.models import async_session, User, Price, Order
import os

async def save_user(tg_id: int, username: str, first_name: str, last_name: str):
    async with async_session() as session:
        user = await session.execute(select(User).where(User.tg_id == tg_id))
        user = user.scalar_one_or_none()

        if not user:
            new_user = User(tg_id=tg_id, username=username,
                            first_name=first_name, last_name=last_name)
            session.add(new_user)
            await session.commit()
            return 1

async def get_prices():
    try:
        async with async_session() as session:
            prices = await session.scalars(select(Price))
            return {price.name: price.value for price in prices}
    except Exception as e:
        print('Error in take price')
        return {}

async def get_discount(tg_id: int):
    try:
        async with async_session() as session:
            # Запрашиваем пользователя по tg_id
            user = await session.scalar(select(User).where(User.tg_id == tg_id))
            if user:
                # Возвращаем значение скидки
                return user.discount
            else:
                # Если пользователь не найден, возвращаем None или другое подходящее значение
                print('User not found')
                return None
    except Exception as e:
        print(f'Error in get_discount: {e}')
        return None

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
    except Exception:
        print('Error in def save_order')






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
    try:
        async with async_session() as session:
            # Находим пользователя по имени пользователя
            user = await session.scalar(select(User).where(User.username == username))
            if user:
                # Обновляем значение скидки
                stmt = update(User).where(User.username == username).values(discount=discount)
                await session.execute(stmt)
                await session.commit()
                return True
            else:
                print(f"User with username {username} not found")
                return False
    except Exception as e:
        print(f"Error in set_discount: {e}")
        return False


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

# Добавляем функцию для получения user_id заказа
async def get_order_user_id(order_id: int):
    async with async_session() as session:
        order = await session.scalar(select(Order).where(Order.id == order_id))
        return order.user_id if order else None

async def get_last_order_id():
    try:
        async with async_session() as session:
            # Используем func.max для нахождения максимального значения id в таблице Order
            result = await session.scalar(select(func.max(Order.id)))
            if result is not None:
                return result
            else:
                return "No orders found"
    except Exception as e:
        print(f"Error in get_last_order_id: {e}")
        return None

# Добавляем функцию для проверки, забанен ли пользователь
async def is_user_banned(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User.is_banned).where(User.tg_id == tg_id))
        return user if user is not None else False

# Функция для бана пользователя
async def ban_user(tg_id: int):
    async with async_session() as session:
        stmt = update(User).where(User.tg_id == tg_id).values(is_banned=True)
        await session.execute(stmt)
        await session.commit()

# Функция для разбанивания пользователя
async def unban_user(tg_id: int):
    async with async_session() as session:
        stmt = update(User).where(User.tg_id == tg_id).values(is_banned=False)
        await session.execute(stmt)
        await session.commit()

async def get_order_user_id(order_id: int) -> int:
    async with async_session() as session:
        result = await session.scalar(select(Order.user_id).where(Order.id == order_id))
        return result


async def update_order_status(order_id: int, status: str):
    async with async_session() as session:
        # Получаем текущий статус заказа
        current_status = await session.scalar(select(Order.status).where(Order.id == order_id))


        if current_status == status:
            # Статус заказа уже такой же, как и новый статус
            return 2
        elif current_status == "None":
            # Обновляем статус заказа
            stmt = update(Order).where(Order.id == order_id).values(status=status)
            await session.execute(stmt)
            await session.commit()
            return 1
        else:
            return 0