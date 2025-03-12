from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def user_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🎁 Получить подарок")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def request_contact_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📲 Отправить контакт", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def admin_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 Одобренные заявки", callback_data="approved_list")]
    ])

def review_controls_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data="approve"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data="reject")
        ],
        [InlineKeyboardButton(text="⏹ Стоп", callback_data="stop")]
    ])