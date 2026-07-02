import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

# Твои данные уже внутри
BOT_TOKEN = "8251049495:AAHZLmdLdvvQQDviJuOmeZYGCempa7ElbZI"
ADMIN_ID = 7323439693 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class OrderForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_category = State()
    waiting_for_description = State()

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        "Привет! Я бот для приёма заявок. Давайте оформим ваш запрос.\n"
        "Как к вам можно обращаться? (Введите ваше имя)"
    )
    await state.set_state(OrderForm.waiting_for_name)

@dp.message(OrderForm.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    
    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Поделиться контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"Приятно познакомиться, {message.text}! Теперь укажите ваш номер телефона. "
        f"Можно ввести вручную или нажать кнопку ниже.",
        reply_markup=phone_keyboard
    )
    await state.set_state(OrderForm.waiting_for_phone)

@dp.message(OrderForm.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text

    await state.update_data(phone=phone)
    
    category_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 Ремонт смартфона", callback_data="cat_phone")],
            [InlineKeyboardButton(text="💻 Ремонт ноутбука", callback_data="cat_laptop")],
            [InlineKeyboardButton(text="🖥️ Ремонт ПК", callback_data="cat_pc")],
            [InlineKeyboardButton(text="⚙️ Другое", callback_data="cat_other")]
        ]
    )
    
    await message.answer(
        "Выберите категорию вашей проблемы:",
        reply_markup=category_keyboard
    )
    await state.set_state(OrderForm.waiting_for_category)

@dp.callback_query(OrderForm.waiting_for_category, F.data.startswith("cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    categories = {
        "cat_phone": "📱 Ремонт смартфона",
        "cat_laptop": "💻 Ремонт ноутбука",
        "cat_pc": "🖥️ Ремонт ПК",
        "cat_other": "⚙️ Другое"
    }
    
    chosen_cat = categories.get(callback.data, "Неизвестно")
    await state.update_data(category=chosen_cat)
    
    await callback.answer()
    await callback.message.edit_text(f"Выбранная категория: **{chosen_cat}**\n\nТеперь подробно опишите суть проблемы:")
    await state.set_state(OrderForm.waiting_for_description)

@dp.message(OrderForm.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    user_data = await state.get_data()
    
    await message.answer(
        "Спасибо! Ваша заявка успешно принята. Мы свяжемся с вами в ближайшее время.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Красивый шаблон заявки
    admin_text = (
        f"🔔 **Новая заявка!**\n\n"
        f"👤 **Клиент:** {user_data['name']}\n"
        f"📞 **Телефон:** {user_data['phone']}\n"
        f"📁 **Категория:** {user_data['category']}\n"
        f"💬 **Юзернейм:** @{message.from_user.username if message.from_user.username else 'нет'}\n"
        f"📝 **Описание:** {user_data['description']}"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение админу: {e}")
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
