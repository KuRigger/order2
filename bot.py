import re
import os
import asyncio
import logging
import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_PASSWORD, GIFT_PDF_PATH
from storage import approved_storage
from states import UserForm, AdminPanel
from keyboards import *
from utils.excel_export import export_to_excel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_existing_application(user_id: int, email: str, phone: str) -> bool:
    return any([
        approved_storage.find(lambda x: x['user_id'] == user_id),
        approved_storage.find(lambda x: x['email'] == email),
        approved_storage.find(lambda x: x['phone'] == phone)
    ])

async def send_gift(user_id: int, bot: Bot):
    try:
        with open(GIFT_PDF_PATH, 'rb') as f:
            await bot.send_document(
                chat_id=user_id,
                document=types.BufferedInputFile(f.read(), filename="Инструкция.pdf"),
                caption="🎁 Ваш подарок!"
            )
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки подарка: {e}")
        return False

async def main():
    try:
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        print("Бот инициализирован!")

        # ================== User Handlers ==================

        @dp.message(F.text == "/start")
        async def cmd_start(message: types.Message):
            await message.answer("Добро пожаловать! 🎉\n"
            "Для получения подарка нажмите кнопку:",
            reply_markup=user_main_kb()
            )

        @dp.message(F.text == "🎁 Получить подарок")
        async def start_form(message: types.Message, state: FSMContext):
            existing = await check_existing_application(
                user_id=message.from_user.id,
                email="",
                phone=""
            )
            
            if existing:
                await message.answer("❌ Вы уже получали подарок!")
                return

            # Начинаем новый опрос
            await state.set_state(UserForm.name)
            await message.answer(
                "📝 Для начала введите ваше ФИО:",
                reply_markup=types.ReplyKeyboardRemove()
            )

        @dp.message(UserForm.name)
        async def process_name(message: types.Message, state: FSMContext):
            await state.update_data(name=message.text, user_id=message.from_user.id)
            await state.set_state(UserForm.email)
            await message.answer("📧 Ваш email адрес?")

        @dp.message(UserForm.email)
        async def process_email(message: types.Message, state: FSMContext):
            if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", message.text):
                await message.answer("❌ Некорректный email! Введите снова:")
                return
            await state.update_data(email=message.text)
            await state.set_state(UserForm.birth_year)
            await message.answer("Год вашего рождения?")

        @dp.message(UserForm.birth_year)
        async def process_birth_year(message: types.Message, state: FSMContext):
            current_year = datetime.datetime.now().year
            try:
                year = int(message.text)
                if not (1900 < year <= current_year):
                    raise ValueError
            except ValueError:
                await message.answer(f"❌ Год должен быть числом между 1900 и {current_year}!")
                return
            
            await state.update_data(birth_year=year)
            await state.set_state(UserForm.contact)
            await message.answer(
                "👌 Последний шаг - поделитесь контактом:",
                reply_markup=request_contact_kb()
            )

        @dp.message(UserForm.contact, F.contact)
        async def process_contact(message: types.Message, state: FSMContext):
            data = await state.get_data()
            data['phone'] = message.contact.phone_number
            
            if await check_existing_application(
                user_id=message.from_user.id,
                email=data['email'],
                phone=data['phone']
            ):
                await message.answer("❌ Вы уже получали подарок!")
                await state.clear()
                return

            # Сохраняем в approved и отправляем подарок
            approved_storage.add(data)
            await send_gift(message.from_user.id, bot)
            await state.clear()

        # ================== Admin Handlers ==================
        @dp.message(F.text == "/admin")
        async def admin_start(message: types.Message, state: FSMContext):
            await state.set_state(AdminPanel.auth)
            await message.answer("🔑 Введите пароль администратора:")

        @dp.message(AdminPanel.auth)
        async def admin_auth(message: types.Message, state: FSMContext):
            if message.text != ADMIN_PASSWORD:
                await message.answer("❌ Неверный пароль!")
                return await state.clear()
            
            await state.set_state(AdminPanel.main)
            await message.answer(
                "Панель администратора:",
                reply_markup=admin_main_kb()
            )

        @dp.callback_query(F.data == "approved_list")
        async def show_approved_list(callback: types.CallbackQuery, state: FSMContext):
            approved = approved_storage.data
            if not approved:
                await callback.answer("📭 Список одобренных заявок пуст")
                return

            filename = export_to_excel(approved)
            with open(filename, 'rb') as f:
                await callback.message.answer_document(
                    document=types.BufferedInputFile(f.read(), filename=filename),
                    caption="📊 Выгрузка одобренных заявок"
                )
            os.remove(filename)
            await callback.answer()

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot) 

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())