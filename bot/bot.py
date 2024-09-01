import random
from io import BytesIO
from time import timezone
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import BufferedInputFile
from aiogram import Router
from aiogram.filters import Command
from PIL import Image, ImageDraw, ImageFont
import asyncio
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '6804578580:AAEdX8AJJP5-mhmM04XTonBr_SQ9HWR1pAU'
API_ENDPOINT = 'http://127.0.0.1:8000/api/' 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

router = Router()

user_captchas = {}
user_data = {}
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

        await call.message.answer(order_details, reply_markup=keyboard)
    else:
        await call.message.answer("Buyurtma yaratishda xatolik yuz berdi.")

@router.callback_query(lambda call: call.data.startswith("cancel_order_"))
async def cancel_order(call: types.CallbackQuery):
    order_id = call.data.split("_")[2]
    response = requests.delete(f'{API_ENDPOINT}order/{order_id}/')

    if response.status_code == 204:
        await call.message.answer(f"Buyurtma ID: #{order_id} bekor qilindi va o'chirildi.")
    else:
        await call.message.answer("Buyurtmani bekor qilishda xatolik yuz berdi.")
@router.callback_query(lambda call: call.data.startswith("pay_order_"))
async def handle_payment(call: types.CallbackQuery):
    order_id = call.data.split("_")[2]
    
    user_id = call.from_user.id
    user_data[user_id]["order_id"] = order_id
    
    await call.message.answer("Iltimos, to'lov summasini kiriting:")
    await call.message.answer("To'lov summasini kiritganingizdan so'ng, chek rasmni yuboring.")
    
    user_data[user_id]["payment_state"] = "amount"

@router.message()
async def handle_payment_details(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in user_data and "payment_state" in user_data[user_id]:
        if user_data[user_id]["payment_state"] == "amount":
            try:
                payment_amount = int(message.text)
                user_data[user_id]["payment_amount"] = payment_amount
                user_data[user_id]["payment_state"] = "receipt"
                
                await message.answer("Iltimos, to'lov chekining rasmni yuboring:")
            except ValueError:
                await message.answer("Iltimos, to'lov summasini raqam sifatida kiriting.")
        elif user_data[user_id]["payment_state"] == "receipt":
            if message.photo:
                photo_id = message.photo[-1].file_id
                user_data[user_id]["receipt_photo"] = photo_id
                await save_payment_info(user_id)
                await message.answer("To'lov muvaffaqiyatli qabul qilindi.")
                user_data[user_id].pop("payment_state", None)  
            else:
                await message.answer("Iltimos, rasm yuboring.")
        else:
            await message.answer("Noaniq buyruq. Iltimos, /start buyrug'ini kiriting.")
    else:
        await message.answer("Iltimos, avval buyurtma yarating.")

async def save_payment_info(user_id):
    order_id = user_data[user_id]["order_id"]
    payment_amount = user_data[user_id].get("payment_amount")
    receipt_photo = user_data[user_id].get("receipt_photo")
    
    order_data = {
        "payment_amount": payment_amount,
        "receipt_photo": receipt_photo
    }
    response = requests.patch(f'{API_ENDPOINT}orders/{order_id}/', data=order_data)
    
    if response.status_code == 200:
        pass
    else:
        print("Error updating payment information.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())