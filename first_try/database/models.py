from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = 'sqlite+aiosqlite:///db.sqlite3'

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    username = Column(String, index=True)
    file_name = Column(String)
    num_pages = Column(Integer)
    total_cost = Column(Float)
    timestamp = Column(DateTime, default=func.now())

class Price(Base):
    __tablename__ = 'prices'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    value = Column(Float)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)