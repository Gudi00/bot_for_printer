from sqlalchemy import BigInteger, String, Column, Integer, Float, DateTime, func, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

DATABASE_URL = 'sqlite+aiosqlite:///db.sqlite3'

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    ref = Column(BigInteger, index=True, default=0)
    #birthday = date
    discount = Column(Float, default=0.0)
    is_banned = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=func.now())
    messages = Column(Integer, index=True, default=0)
    messages_from_last_order = Column(Integer, index=True, default=0)


class Price(Base):
    __tablename__ = 'prices'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    value = Column(Float)
    name_for_user = Column(String, unique=True)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True)
    username = Column(String, index=True)
    file_name = Column(String)
    num_pages = Column(Integer)
    total_cost = Column(Float)
    timestamp = Column(DateTime, default=func.now())
    status = Column(String, default='None')

class Money(Base): #дополнить (автооплата, скидка для постоянных клиетов на основе алгоритма)
    __tablename__ = 'all_money'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True)
    username = Column(String, index=True)
    discount = Column(Float, index=True, default=0)
    free_paper = Column(Integer, index=True, default=0)
    money = Column(Float, index=True, default=0)
    number_of_orders_per_week = Column(Integer, index=True, default=0)
    number_of_completed_orders = Column(Integer, index=True, default=0)
    number_of_orders = Column(Integer, index=True, default=0)


class Admin_state(Base):
    __tablename__ = 'admin_states'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True)
    username = Column(String, index=True)
    free_time = Column(String, index=True)
    timestamp = Column(DateTime, default=func.now())

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
