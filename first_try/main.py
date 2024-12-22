import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers.main_handlers import register_main_handlers
from handlers.admin_handlers import register_admin_handlers
from database.models import async_main
from config import load_config
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    config = load_config()
    await async_main()

    bot = Bot(token=config['BOT_TOKEN'])
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров
    register_main_handlers(dp)
    register_admin_handlers(dp)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Error during polling: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')