from sqlalchemy import select, update, func, desc
from app.database.models import async_session, User, Price, Order, Money
import os

async def save_user(tg_id: int, username: str, first_name: str, last_name: str):
    async with async_session() as session:
        user = await session.execute(select(User).where(User.tg_id == tg_id))
        user = user.scalar_one_or_none()

        if not user:
            new_user = User(tg_id=tg_id, username=username,
                            first_name=first_name, last_name=last_name)
            session.add(new_user)
            new_user = Money(user_id=tg_id, username=username)
            session.add(new_user)
            await session.commit()
            return 1

async def get_number_of_orders_per_week():
    async with async_session() as session:
        orders = await session.scalars(select(Money))
        return orders

async def get_prices():
    try:
        async with async_session() as session:
            prices = await session.scalars(select(Price))
            return {price.name: price.value for price in prices}
    except Exception as e:
        print('Error in take price')
        return {}

async def get_prices_for_command():
    try:
        async with async_session() as session:
            prices = await session.scalars(select(Price))
            return {price.name_for_user: price.value for price in prices}
    except Exception as e:
        print('Error in take price')
        return {}

async def generate_discount_message_admin(prices):
    message = ""
    discounts = range(0, 100, 10)  # Скидки от 0% до 90% с шагом 10%

    for name, value in prices.items():
        message += f"{name}:\n\n"
        for discount in discounts:
            discounted_value = value * (1 - discount / 100)
            message += f"{discount}% - {discounted_value:.2f} рублей\n"
        message += "\n"

    return message

async def getNoneOrders():
    async with async_session() as session:
        prices = await session.scalars(select(Order))
        message = "Нужно выполнить:\n"

        for price in prices:
            message += f"Заказ номер: {price.id} от @{price.username}\n"
        return message

async def get_id_all_users():
    async with async_session() as session:
        users = await session.scalars(select(User))
        return users

async def generate_discount_message_user(prices, user_discount):
    message = f"Ваши цены с учётом вашей {user_discount} скидкой:\n\n"
    for name, value in prices.items():
        # Добавляем стоимость с учётом индивидуальной скидки пользователя
        user_discounted_value = value * (1 - user_discount)
        message += f"{name}: {user_discounted_value:.2f} рублей\n"
    return message



async def get_discount(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        return float(user.discount)

async def fetch_user_money(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(Money).where(Money.user_id == tg_id))
        user = result.scalar_one_or_none()
        return float(user.money)

async def update_referral(username: str, user_id: int):
    async with async_session() as session:
        async with session.begin():
            if username[0] == '@':
                username = username[1:]

            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            if user:
                ref_value = user.tg_id
                result = await session.execute(
                    select(User).where(User.tg_id == user_id)
                )
                user = result.scalar_one_or_none()
                if user.ref == 0:
                    stmt = update(User).where(User.tg_id == user_id).values(
                        ref=ref_value)  # Создаем запрос на обновление
                    await session.execute(stmt)  # Выполняем запрос
                    await session.commit()
                    disc = await get_discount(user_id)

                    if disc < 0.1:
                        disc = 0.1
                        await set_discount(user_id, 0.1)
                    return disc, ref_value
                return 1, 0
            return 0, 0

async def get_last_order_number(user_id: int):
    async with async_session() as session:
        # Выполняем запрос к таблице orders
        result = await session.execute(
            select(Order).where(Order.user_id == user_id).order_by(desc(Order.id))
        )
        # Получаем последний заказ
        last_order = result.scalars().first()
        # Возвращаем номер заказа, если заказ найден, иначе None
        return last_order.id if last_order else None

async def get_number_of_orders_per_week(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(Money).where(Money.user_id == tg_id))
        user = result.scalar_one_or_none()
        return int(user.number_of_orders_per_week)

async def get_ref(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        return int(user.ref)

async def get_messages_from_last_order(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        return int(user.messages_from_last_order)

async def get_number_of_orders(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(Money).where(Money.user_id == tg_id))
        user = result.scalar_one_or_none()
        return int(user.number_of_orders)

async def get_number_of_completed_orders(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(Money).where(Money.user_id == tg_id))
        user = result.scalar_one_or_none()
        return int(user.number_of_completed_orders)

async def get_number_of_completed_orders(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(Money).where(Money.user_id == tg_id))
        user = result.scalar_one_or_none()
        return int(user.number_of_completed_orders)

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

async def set_discount(user_id: str, discount: float):
    if discount <= 1:
        try:
            async with async_session() as session:  # Открываем сессию
                stmt = update(User).where(User.tg_id == user_id).values(
                    discount=discount)  # Создаем запрос на обновление
                result = await session.execute(stmt)  # Выполняем запрос
                await session.commit()  # Фиксируем изменения

                # Проверяем количество затронутых строк
                if result.rowcount > 0:
                    return True
                else:
                    return False

        except Exception as e:
            print(f"Error in set_discount: {e}")
            return False
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




async def update_money(user_id: int, bill: float):
    async with async_session() as session:
        result = await session.execute(select(Money).where(Money.user_id == user_id))
        user = result.scalars().first()

        was = float(user.money)
        new = was + bill


        # Обновление данных пользователя
        stmt = (
            update(Money)
            .where(Money.user_id == user_id)
            .values(money=new)
        )
        await session.execute(stmt)
        await session.commit()
        if new >= 0:
            return (f"Стоимость заказа: 0.00 рубелй. Сумма, равная стоимости вашего заказа ({round(abs(bill), 2)} рублей),"
                    f" была cписана с вашего счёта. Ваш остаток: {round(new, 2)} рублей")
        elif round(was, 2) != 0:
            return f"Стоимость заказа: {round(abs(bill), 2)}. Вам следует донести {round(abs(new), 2)} рублей"
        else:
            return f"Стоимость заказа: {round(abs(bill), 2)}"

async def update_number_of_orders(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Money).where(Money.user_id == user_id))
        user = result.scalars().first()

        new = int(user.number_of_orders) + 1

            # Обновление данных пользователя
        stmt = (
            update(Money)
            .where(Money.user_id == user_id)
            .values(number_of_orders=new)
        )
        await session.execute(stmt)
        await session.commit()

async def update_number_of_orders_per_week(user_id: int, new: int):
    async with async_session() as session:
            # Обновление данных пользователя
        stmt = (
            update(Money)
            .where(Money.user_id == user_id)
            .values(number_of_orders_per_week=new)
        )
        await session.execute(stmt)
        await session.commit()


async def update_number_of_completed_orders(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Money).where(Money.user_id == user_id))
        user = result.scalars().first()

        new = int(user.number_of_completed_orders) + 1

            # Обновление данных пользователя
        stmt = (
            update(Money)
            .where(Money.user_id == user_id)
            .values(number_of_completed_orders=new)
        )
        await session.execute(stmt)
        await session.commit()

async def update_number_of_messages(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalars().first()

        new = int(user.messages) + 1

            # Обновление данных пользователя
        stmt = (
            update(User)
            .where(User.tg_id == user_id)
            .values(messages=new)
        )
        await session.execute(stmt)
        await session.commit()

async def update_number_of_messages_from_last_order(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalars().first()

        new = int(user.messages_from_last_order) + 1

            # Обновление данных пользователя
        stmt = (
            update(User)
            .where(User.tg_id == user_id)
            .values(messages_from_last_order=new)
        )
        await session.execute(stmt)
        await session.commit()



async def populate_prices():
    async with async_session() as session:
        prices = [
            {"name": "my_paper_1", "value": 0.25, "name_for_user": "1 лист"},
            {"name": "my_paper_2_5", "value": 0.2, "name_for_user": "с 2 до 5 листов"},
            {"name": "my_paper_6_20", "value": 0.17, "name_for_user": "с 6 до 20 листов"},
            {"name": "my_paper_21_150", "value": 0.15, "name_for_user": "с 21 до 150 листов"},
        ]

        for price in prices:
            # Проверка, существует ли уже запись с таким именем
            result = await session.execute(select(Price).where(Price.name == price["name"]))
            existing_price = result.scalars().first()

            if not existing_price:
                new_price = Price(
                    name=price["name"],
                    value=price["value"],
                    name_for_user=price["name_for_user"],
                )
                session.add(new_price)

        await session.commit()



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

async def damp_messages_from_last_order(tg_id: int):
    async with async_session() as session:
        stmt = update(User).where(User.tg_id == tg_id).values(messages_from_last_order=0)
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

async def get_none_orders():##
    try:
        async with async_session() as session:
            orders = await session.scalars(select(Order))
            return {order.id: order.status for order in orders}
    except Exception as e:
        print('Error in take price')
        return {}

async def get_user_discount():##
    try:
        async with async_session() as session:
            users = await session.scalars(select(User))
            return {user.username: user.discount for user in users}
    except Exception as e:
        print('Error in take price')
        return {}