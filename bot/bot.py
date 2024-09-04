import random
import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import telebot
from telebot import types
import requests
import aiohttp
import asyncio

API_TOKEN = "6804578580:AAEoZCZLRNUmr36YOWmriEO9HSVMsjTVOnc"  # Replace with your actual bot token
API_ENDPOINT = "http://127.0.0.1:8000/"  # Replace with your Django server URL

bot = telebot.TeleBot(API_TOKEN)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_captchas = {}
user_data = {}
order_message_ids = {}

# Generate CAPTCHA
def generate_captcha():
    captcha_text = str(random.randint(100000, 999999))
    background = Image.open("bot/s.jpg").convert("RGBA")
    image = background.resize((200, 100))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arialbd.ttf", size=36)

    for i, char in enumerate(captcha_text):
        x = random.randint(10 + i * 30, 30 + i * 30)
        y = random.randint(20, 50)
        draw.text((x, y), char, font=font, fill=(0, 0, 0))

    logger.info(f"Captcha generated: {captcha_text}")
    return captcha_text, image

@bot.message_handler(commands=['start'])
def send_captcha_or_greet(message):
    user_id = message.from_user.id
    logger.info(f"/start command received from user {user_id}")

    response = requests.get(f'{API_ENDPOINT}users/{user_id}/')

    if response.status_code == 200:
        logger.info(f"User {user_id} is already registered.")
        bot.send_message(message.chat.id, "Привет! Пожалуйста")
        send_city_selection(message)
    elif response.status_code == 404:
        logger.info(f"User {user_id} is not registered, sending captcha.")
        captcha_text, captcha_image = generate_captcha()

        bio = BytesIO()
        captcha_image.save(bio, format='PNG')
        bio.seek(0)

        bot.send_photo(message.chat.id, photo=bio, caption="Пожалуйста, отправьте код, показанный на изображении:")
        bio.close()  # Xotirani tozalash uchun obyektni yopamiz

        user_captchas[user_id] = {
            "captcha_text": captcha_text,
            "name": message.from_user.first_name,
            "username": message.from_user.username
        }
    else:
        logger.error(f"Error checking user {user_id} registration status. HTTP Status: {response.status_code}")
        bot.send_message(message.chat.id, "Произошла ошибка. Повторите попытку позже.")

@bot.message_handler(func=lambda message: user_captchas.get(message.from_user.id))
def process_captcha_response(message):
    user_id = message.from_user.id
    if user_id in user_captchas:
        captcha_text = user_captchas[user_id]["captcha_text"]
        logger.info(f"Received captcha response from user {user_id}: {message.text}")

        if message.text == captcha_text:
            data = {
                "telegram_id": user_id,
                "name": user_captchas[user_id]["name"],
                "username": user_captchas[user_id]["username"],
            }
            response = requests.post(f'{API_ENDPOINT}users/', json=data)
            if response.status_code == 201:
                logger.info(f"User {user_id} successfully registered.")
                bot.send_message(message.chat.id, "Привет! Вы зарегистрировались.")
                send_city_selection(message)
            else:
                logger.error(f"Failed to register user {user_id}. HTTP Status: {response.status_code}")
                bot.send_message(message.chat.id, "Во время регистрации произошла ошибка. Повторите попытку позже.")
            del user_captchas[user_id]
        else:
            logger.warning(f"Incorrect captcha response from user {user_id}. Expected: {captcha_text}, Got: {message.text}")
            bot.send_message(message.chat.id, "Код ошибки. Пожалуйста, попробуйте еще раз.")

def send_city_selection(message):
    response = requests.get(f'{API_ENDPOINT}shaxar/')
    cities_data = response.json()
    cities = cities_data.get('results', [])

    if cities:
        keyboard = types.InlineKeyboardMarkup()
    
        row = []
        for index, city in enumerate(cities):
            button = types.InlineKeyboardButton(text=city['nomi'], callback_data=f"city_{city['id']}")
            row.append(button)
            
            if (index + 1) % 2 == 0:
                keyboard.row(*row)
                row = []
    
        if row:
            keyboard.row(*row)

        keyboard.add(
            types.InlineKeyboardButton(
                text="Условия перезаклада",
                url="https://telegra.ph/Pretenzii-po-nenahodu-09-03"
            )
        )

        # Send the message with the keyboard
        bot.send_message(message.chat.id, "Выберите город:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Hozircha hech qanday shahar mavjud emas.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("city_"))
def send_product_selection(call):
    user_id = call.from_user.id
    city_id = call.data.split("_")[1]
    user_data[user_id] = {"city_id": city_id, "name": call.from_user.first_name}

    response = requests.get(f'{API_ENDPOINT}mahsulot/?shaxar_id={city_id}')
    products = response.json().get('results', [])

    if products:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        for product in products:
            button = types.InlineKeyboardButton(text=product['nomi'], callback_data=f"product_{product['id']}")
            keyboard.add(button)
        bot.send_message(call.message.chat.id, "Выберите товар:", reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, "Bu shahar uchun hech qanday mahsulot mavjud emas.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def send_rayon_selection(call):
    user_id = call.from_user.id
    product_id = call.data.split("_")[1]
    user_data[user_id]["product_id"] = product_id

    response = requests.get(f'{API_ENDPOINT}rayon/?mahsulot_id={product_id}')
    regions = response.json().get('results', [])

    if regions:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        for region in regions:
            button = types.InlineKeyboardButton(text=region['nomi'], callback_data=f"region_{region['id']}")
            keyboard.add(button)
        bot.send_message(call.message.chat.id, "Выберите район:", reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, "Bu mahsulot uchun hech qanday rayon mavjud emas.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("region_"))
def send_korinish_selection(call):
    user_id = call.from_user.id
    region_id = call.data.split("_")[1]
    user_data[user_id]["region_id"] = region_id

    response = requests.get(f'{API_ENDPOINT}korinish/?rayon_id={region_id}')
    types_ = response.json().get('results', [])

    if types_:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        for korinish in types_:
            button = types.InlineKeyboardButton(text=korinish['nomi'], callback_data=f"korinish_{korinish['id']}")
            keyboard.add(button)
        bot.send_message(call.message.chat.id, "Вид товара:", reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, "Bu rayon uchun hech qanday ko'rinish mavjud emas.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("korinish_"))
def create_order(call):
    user_id = call.from_user.id
    korinish_id = call.data.split("_")[1]
    user_data[user_id]["korinish_id"] = korinish_id

    # Fetching city, product, region, and type names
    city_name = requests.get(f'{API_ENDPOINT}shaxar/{user_data[user_id]["city_id"]}/').json().get('nomi', 'Unknown')
    product_name = requests.get(f'{API_ENDPOINT}mahsulot/{user_data[user_id]["product_id"]}/').json().get('nomi', 'Unknown')
    narxi = requests.get(f'{API_ENDPOINT}mahsulot/{user_data[user_id]["product_id"]}/').json().get('narxi', 'Unknown')
    region_name = requests.get(f'{API_ENDPOINT}rayon/{user_data[user_id]["region_id"]}/').json().get('nomi', 'Unknown')
    type_name = requests.get(f'{API_ENDPOINT}korinish/{korinish_id}/').json().get('nomi', 'Unknown')

    user_name = user_data[user_id].get("name", 'Anonymous')

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

        # Save order_id to user_data
        user_data[user_id]["order_id"] = order_id

        order_details = (
            f"Идентификатор вашей покупки: #{order_id}\n\n"

            f"Товар и объем: {product_name}\n"
            f"Сумма к оплате: {narxi} сум\n"
            f"Местоположение: {city_name}\n"            
            f"Локация/Ближащая станция: {region_name}\n"
            f"Заказанное время: {created_at}\n\n"
            "Пожалуйста, перейдите к оплате, нажав кнопку ОПЛАТИТЬ.\nОбратите внимание: после начала процесса оплаты у вас будет 48 час для её завершения."
        )
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(text="Оплатит", callback_data=f"pay_order_{order_id}"),
            types.InlineKeyboardButton(text="Отмена", callback_data=f"cancel_order_{order_id}")
        )

        msg = bot.send_message(call.message.chat.id, order_details, reply_markup=keyboard)
        order_message_ids[user_id] = msg.message_id
    else:
        bot.send_message(call.message.chat.id, "Buyurtmani yaratishda xatolik yuz berdi. Keyinroq qayta urinib ko'ring.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_order_"))
def handle_payment(call):
    order_id = call.data.split("_")[2]
    user_id = call.from_user.id
    user_data[user_id]["order_id"] = order_id
    narxi = requests.get(f'{API_ENDPOINT}mahsulot/{user_data[user_id]["product_id"]}/').json().get('narxi', 'Unknown')

    # Fetch and display cards
    async def fetch_cards():
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{API_ENDPOINT}card/') as response:
                if response.status == 200:
                    data = await response.json()
                    card_data = data.get("results", [])

                    if card_data:
                        keyboard = types.InlineKeyboardMarkup(row_width=2)
                        for card in card_data:
                            keyboard.add(
                                types.InlineKeyboardButton(
                                    text=card['card_name'],
                                    callback_data=f"select_card_{card['id']}"
                                )
                            )
                        keyboard.add(
                            types.InlineKeyboardButton(
                                text="Через администратора",
                                url=f"t.me/sayfullayev_0204"  # Replace with admin's username
                            )
                        )
                        bot.send_message(call.message.chat.id, f"Ваш актуальный баланс {narxi}.\nЧем вы будете оплачивать?", reply_markup=keyboard)
                    else:
                        bot.send_message(call.message.chat.id, "Karta ma'lumotlari topilmadi yoki karta ro'yxati bo'sh.")
                else:
                    bot.send_message(call.message.chat.id, "Karta ma'lumotlarini olishda xatolik yuz berdi.")
    import asyncio
    asyncio.run(fetch_cards())
@bot.callback_query_handler(lambda call: call.data.startswith("select_card_"))
def display_card_details(call):
    card_id = call.data.split("_")[2]
    user_id = call.from_user.id

    async def fetch_card_details():
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{API_ENDPOINT}card/{card_id}/') as response:
                if response.status == 200:
                    card = await response.json()
                    card_info = (
                        f"Имя карты: {card['card_name']}\n"
                        f"Пользователь карты: {card['card_user']}\n"
                        f"Номер карты: {card['card_number']}"
                    )

                    pay_button = types.InlineKeyboardMarkup()
                    pay_button.add(
                        types.InlineKeyboardButton(
                            text="Внести платеж",
                            callback_data=f"confirm_payment_{user_data[user_id]['order_id']}_{card_id}"
                        )
                    )
                    
                    bot.send_message(call.message.chat.id, f"Информация о карте:\n{card_info}\n\nСовершите платеж на эту карту.", reply_markup=pay_button)
                else:
                    bot.send_message(call.message.chat.id, "Karta ma'lumotlarini olishda xatolik yuz berdi.")
    import asyncio
    asyncio.run(fetch_card_details())

@bot.callback_query_handler(lambda call: call.data.startswith("cancel_order_"))
def cancel_order(call):
    user_id = call.from_user.id
    order_id = call.data.split("_")[2]

    # Delete the order details message
    if user_id in order_message_ids:
        chat_id = call.message.chat.id
        try:
            bot.delete_message(chat_id, order_message_ids[user_id])
        except Exception as e:
            print(f"Failed to delete message: {e}")

    response = requests.delete(f'{API_ENDPOINT}order/{order_id}/')

    if response.status_code == 204:
        bot.send_message(call.message.chat.id, f"Идентификатор заказа: #{order_id} был отменен и удален.")
    else:
        bot.send_message(call.message.chat.id, "Buyurtmani bekor qilishda xatolik yuz berdi.")

@bot.callback_query_handler(lambda call: call.data.startswith("confirm_payment_"))
def request_payment_details(call):
    user_id = call.from_user.id
    order_id, card_id = call.data.split("_")[2], call.data.split("_")[3]

    if user_id in user_data:
        user_data[user_id]["card_id"] = card_id

        bot.send_message(call.message.chat.id, "Пожалуйста, введите сумму платежа:")

@bot.message_handler(func=lambda message: message.text.isdigit() and message.from_user.id in user_data)
def handle_payment_amount(message):
    user_id = message.from_user.id
    if user_id in user_data:
        payment_amount = message.text
        user_data[user_id]["payment_amount"] = payment_amount

        bot.send_message(message.chat.id, "Пожалуйста, загрузите изображение платежа.")

@bot.message_handler(content_types=['photo'])
def handle_payment_receipt(message):
    user_id = message.from_user.id

    if user_id in user_data:
        receipt_photo = message.photo[-1].file_id
        payment_amount = user_data[user_id].get("payment_amount")
        order_id = user_data[user_id].get("order_id")
        card_id = user_data[user_id].get("card_id")

        if payment_amount and order_id:
            file_info = bot.get_file(receipt_photo)
            file_url = f'https://api.telegram.org/file/bot{API_TOKEN}/{file_info.file_path}'
            files = {'receipt_image': (receipt_photo, requests.get(file_url).content)}

            data = {
                "telegram_id": user_id,
                "payment_amount": payment_amount,
            }

            try:
                response = requests.post(f'{API_ENDPOINT}order/{order_id}/payment/', data=data, files=files)
                if response.status_code == 200:
                    bot.send_message(message.chat.id, "Платеж получен, ждем подтверждения...")
                    del user_data[user_id]
                    if user_id in order_message_ids:
                        bot.delete_message(message.chat.id, order_message_ids[user_id])
                        del order_message_ids[user_id]
                else:
                    bot.send_message(message.chat.id, "To'lovni saqlashda xatolik yuz berdi. Keyinroq qayta urinib ko'ring.")
            except requests.RequestException as e:
                bot.send_message(message.chat.id, "Serverga ulanishda xatolik yuz berdi.")
                print(f"Request error: {e}")
        else:
            error_message = "Информация о платеже неполная. Пожалуйста, пришлите соответствующую информацию."
            bot.send_message(message.chat.id, error_message)
    else:
        bot.send_message(message.chat.id, "Ваш заказ не найден. Пожалуйста, начните процесс оплаты с самого начала.")

# Polling loop
bot.polling(none_stop=True)
