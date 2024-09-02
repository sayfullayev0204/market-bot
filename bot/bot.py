import random
from io import BytesIO
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import BufferedInputFile
from aiogram import Router
from aiogram.filters import Command
from PIL import Image, ImageDraw, ImageFont
import asyncio
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
from aiogram.fsm.state import StatesGroup, State

class PaymentStates(StatesGroup):
    waiting_for_receipt = State()

API_TOKEN = '6804578580:AAEdX8AJJP5-mhmM04XTonBr_SQ9HWR1pAU'
API_ENDPOINT = 'http://127.0.0.1:8000/'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

router = Router()

user_captchas = {}
user_data = {}
order_message_ids = {}

def generate_captcha():
    """Generate a random 6-digit number and create an image with a background."""
    captcha_text = str(random.randint(100000, 999999))
    
    background = Image.open("bot/s.jpg").convert("RGBA")
    image = background.resize((200, 100))
    
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arialbd.ttf", size=36)
    
    for i, char in enumerate(captcha_text):
        x = random.randint(10 + i * 30, 30 + i * 30)  
        y = random.randint(20, 50)
        draw.text((x, y), char, font=font, fill=(0, 0, 0))
    
    return captcha_text, image

@router.message(Command("start"))
async def send_captcha_or_greet(message: types.Message):
    user_id = message.from_user.id
    
    response = requests.get(f'{API_ENDPOINT}users/{user_id}/')
    
    if response.status_code == 200:
        await message.answer("Assalomu aleykum! Siz allaqachon ro'yxatdan o'tgansiz. Shaxarlardan birini tanlang:")
        await send_city_selection(message)
    else:
        if response.status_code == 404:
            captcha_text, captcha_image = generate_captcha()
            
            bio = BytesIO()
            captcha_image.save(bio, format='PNG')
            bio.seek(0)
            
            file = BufferedInputFile(bio.read(), filename="captcha.png")
            
            user_captchas[user_id] = {
                "captcha_text": captcha_text,
                "name": message.from_user.first_name,
                "username": message.from_user.username
            }
        
            await message.answer_photo(file, caption="Iltimos, rasmda ko'rsatilgan kodni yuboring:")
        else:
            await message.answer("Xatolik yuz berdi. Keyinroq qayta urinib ko'ring.")

@router.message()
async def check_captcha(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_captchas:
        if message.text == user_captchas[user_id]["captcha_text"]:
            user_data = {
                "telegram_id": user_id,
                "name": user_captchas[user_id]["name"],
                "username": user_captchas[user_id]["username"]
            }
            response = requests.post(f'{API_ENDPOINT}users/', data=user_data)
            
            if response.status_code == 201:
                await message.answer("Assalomu aleykum! Siz muvaffaqiyatli ro'yxatdan o'tdingiz.")
                del user_captchas[user_id]
                await send_city_selection(message)
            else:
                await message.answer("Ro'yxatdan o'tishda xatolik yuz berdi.")
            
            del user_captchas[user_id]  
        else:
            await message.answer("Kod xato. Qayta urinib ko'ring.")
    else:
        await message.answer("Iltimos, /start buyrug'ini kiriting.")

@router.message(Command("start"))
async def send_city_selection(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {"name": message.from_user.first_name}

    response = requests.get(f'{API_ENDPOINT}shaxar/')
    cities_data = response.json()
    cities = cities_data.get('results', [])

    if cities:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=city['nomi'], callback_data=f"city_{city['id']}")] for city in cities
        ])
        await message.answer("Shaharni tanlang:", reply_markup=keyboard)
    else:
        await message.answer("Hozircha hech qanday shahar mavjud emas.")

@router.callback_query(lambda call: call.data.startswith("city_"))
async def send_product_selection(call: types.CallbackQuery):
    user_id = call.from_user.id
    city_id = call.data.split("_")[1]
    user_data[user_id]["city_id"] = city_id

    response = requests.get(f'{API_ENDPOINT}mahsulot/?shaxar_id={city_id}')
    products = response.json().get('results', [])

    if products:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=product['nomi'], callback_data=f"product_{product['id']}")] for product in products
        ])
        await call.message.answer("Mahsulotni tanlang:", reply_markup=keyboard)
    else:
        await call.message.answer("Bu shahar uchun hech qanday mahsulot mavjud emas.")

@router.callback_query(lambda call: call.data.startswith("product_"))
async def send_rayon_selection(call: types.CallbackQuery):
    user_id = call.from_user.id
    product_id = call.data.split("_")[1]
    user_data[user_id]["product_id"] = product_id

    response = requests.get(f'{API_ENDPOINT}rayon/?mahsulot_id={product_id}')
    regions = response.json().get('results', [])

    if regions:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=region['nomi'], callback_data=f"region_{region['id']}")] for region in regions
        ])
        await call.message.answer("Rayonni tanlang:", reply_markup=keyboard)
    else:
        await call.message.answer("Bu mahsulot uchun hech qanday rayon mavjud emas.")

@router.callback_query(lambda call: call.data.startswith("region_"))
async def send_korinish_selection(call: types.CallbackQuery):
    user_id = call.from_user.id
    region_id = call.data.split("_")[1]
    user_data[user_id]["region_id"] = region_id

    response = requests.get(f'{API_ENDPOINT}korinish/?rayon_id={region_id}')
    types_ = response.json().get('results', [])

    if types_:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=korinish['nomi'], callback_data=f"korinish_{korinish['id']}")] for korinish in types_
        ])
        await call.message.answer("Ko'rinishni tanlang:", reply_markup=keyboard)
    else:
        await call.message.answer("Bu rayon uchun hech qanday ko'rinish mavjud emas.")

@router.callback_query(lambda call: call.data.startswith("korinish_"))
async def create_order(call: types.CallbackQuery):
    user_id = call.from_user.id
    korinish_id = call.data.split("_")[1]

    user_data[user_id]["korinish_id"] = korinish_id

    city_name = requests.get(f'{API_ENDPOINT}shaxar/{user_data[user_id]["city_id"]}/').json().get('nomi')
    product_name = requests.get(f'{API_ENDPOINT}mahsulot/{user_data[user_id]["product_id"]}/').json().get('nomi')
    region_name = requests.get(f'{API_ENDPOINT}rayon/{user_data[user_id]["region_id"]}/').json().get('nomi')
    type_name = requests.get(f'{API_ENDPOINT}korinish/{korinish_id}/').json().get('nomi')

    user_name = user_data[user_id].get("name")

    order_data = {
        "telegram_id": user_id,
        "shaxar_id": user_data[user_id]["city_id"],
        "mahsulot_id": user_data[user_id]["product_id"],
        "rayon_id": user_data[user_id]["region_id"],
        "korinish_id": korinish_id,
        "name": user_name  
    }

    response = requests.post(f'{API_ENDPOINT}orders/create_order/', data=order_data)
    
    if response.status_code == 201:
        response_data = response.json()
        order_id = response_data.get('order_id')
        created_at = response_data.get('created_at')
        user_name = response_data.get('user_name')  

        order_details = (
            f"Buyurtma yaratildi:\n"
            f"Order ID: {order_id}\n"
            f"Foydalanuvchi: {user_name}\n"  
            f"Yaratilgan vaqti: {created_at}\n"
            f"Mahsulot: {product_name}\n"
            f"Shahar: {city_name}\n"
            f"Rayon: {region_name}\n"
            f"Ko'rinish: {type_name}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="To'lov qilish", callback_data=f"pay_order_{order_id}")],
            [InlineKeyboardButton(text="Buyurtmani bekor qilish", callback_data=f"cancel_order_{order_id}")]
        ])

        # Send the order details message and store its message ID
        order_message = await call.message.answer(order_details, reply_markup=keyboard)
        order_message_ids[user_id] = order_message.message_id

    else:
        await call.message.answer("Buyurtma yaratishda xatolik yuz berdi.")

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp

@router.callback_query(lambda call: call.data.startswith("pay_order_"))
async def handle_payment(call: types.CallbackQuery):
    order_id = call.data.split("_")[2]
    user_id = call.from_user.id
    user_data[user_id]["order_id"] = order_id

    # API dan barcha kartalarni olish va ularni inline button shaklida ko'rsatish
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{API_ENDPOINT}card/') as response:
            if response.status == 200:
                data = await response.json()
                card_data = data.get("results", [])

                if card_data and isinstance(card_data, list) and len(card_data) > 0:
                    # Inline buttonlar shaklida kartalar nomini ko'rsatamiz
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                    for card in card_data:
                        keyboard.inline_keyboard.append([InlineKeyboardButton(
                            text=card['card_name'], 
                            callback_data=f"select_card_{card['id']}"
                        )])

                    await call.message.answer("Kartani tanlang:", reply_markup=keyboard)
                else:
                    await call.message.answer("Karta ma'lumotlari topilmadi yoki karta ro'yxati bo'sh.")
            else:
                await call.message.answer("Karta ma'lumotlarini olishda xatolik yuz berdi.")

@router.callback_query(lambda call: call.data.startswith("select_card_"))
async def display_card_details(call: types.CallbackQuery):
    card_id = call.data.split("_")[2]
    user_id = call.from_user.id

    # Tanlangan karta ma'lumotlarini olish va ko'rsatish
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{API_ENDPOINT}card/{card_id}/') as response:
            if response.status == 200:
                card = await response.json()
                
                card_info = (
                    f"Card Name: {card['card_name']}\n"
                    f"Card User: {card['card_user']}\n"
                    f"Card Number: {card['card_number']}"
                )

                # To'lovni amalga oshirish tugmasini qo'shish
                pay_button = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="To'lovni amalga oshirish", callback_data=f"confirm_payment_{user_data[user_id]['order_id']}_{card_id}")]
                ])
                
                await call.message.answer(f"Karta ma'lumotlari:\n{card_info}\n\nUshbu kartaga to'lovni amalga oshiring.", reply_markup=pay_button)
            else:
                await call.message.answer("Karta ma'lumotlarini olishda xatolik yuz berdi.")



@router.callback_query(lambda call: call.data.startswith("cancel_order_"))
async def cancel_order(call: types.CallbackQuery):
    user_id = call.from_user.id
    order_id = call.data.split("_")[2]
    
    # Delete the order details message
    if user_id in order_message_ids:
        chat_id = call.message.chat.id
        try:
            await bot.delete_message(chat_id, order_message_ids[user_id])
        except Exception as e:
            print(f"Failed to delete message: {e}")
    
    response = requests.delete(f'{API_ENDPOINT}order/{order_id}/')

    if response.status_code == 204:
        await call.message.answer(f"Buyurtma ID: #{order_id} bekor qilindi va o'chirildi.")
        await send_city_selection(call.message)
    else:
        await call.message.answer("Buyurtmani bekor qilishda xatolik yuz berdi.")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
