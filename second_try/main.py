import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.handlers import register_main_handlers
from app.admin_handlers import register_admin_handlers
from app.database.models import async_main
from app.config import load_config

from app.database.requests import populate_prices

async def main():
    config = load_config()
    await async_main()

    bot = Bot(token=config['BOT_TOKEN'])
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров
    register_main_handlers(dp)
    register_admin_handlers(dp)

    await populate_prices()

    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        print("Бот работает")
        asyncio.run(main())

    except KeyboardInterrupt:
        print('Бот выключен')
