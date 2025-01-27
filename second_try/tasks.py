# from aiogram import Bot
# from app.database.requests import get_all_users, update_user_streaks, get_info
# from datetime import datetime, timedelta
#
#
# async def send_streak_report(bot: Bot):
#     # Обновление данных стрика
#
#     prices = await get_info()
#
#     # Формируем текст сообщения только для тех пользователей, у которых метка времени не старше одного дня
#     prices_text = "\n".join(
#         [f"@{name}" for name, value in prices.items() if value + timedelta(days=1) < datetime.now()])
#
#     # Проверка, что текст сообщения не пустой
#     if prices_text:
#         await bot.send_message(chat_id='-1002206509266', text=f"{prices_text}\nЛенивый(е)")
#
#     await update_user_streaks()
#
#     users = await get_all_users()
#     message = "Статистика стриков пользователей:\n\n"
#
#     for user in users:
#         message += f"Пользователь {user.username}: {user.streak_days} дней\n"
#
#     await bot.send_message(chat_id='-1002206509266', text=message)