from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Создать заказ')]
], resize_keyboard=True, input_field_placeholder="Выберите опцию")