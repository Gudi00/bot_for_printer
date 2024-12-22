import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.handlers import router as main_router
from app.admin_handlers import router as admin_router
from app.database.models import async_main
from first_try.app.config import load_config


async def main():
    config = load_config()
    await async_main()

    bot = Bot(token=config['BOT_TOKEN'])
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(main_router)
    dp.include_router(admin_router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')