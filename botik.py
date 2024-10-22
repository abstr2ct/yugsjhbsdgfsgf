import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder

API_TOKEN = '7681732840:AAH21CATzaJNXfIDOyxyWXJy5APw_IAAocA' 
WEATHER_API_KEY = 'c69802765d76a5eae88e63d4ca620e7c'
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
class WeatherStates(StatesGroup):
    city = State()
    frequency = State()
def get_weather(city):
    params = {
        'q': city,
        'appid': WEATHER_API_KEY,
        'units': 'metric',
        'lang': 'ru'
    }
   
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        description = data['weather'][0]['description']
        temp = data['main']['temp']
        wind_speed = data['wind']['speed']
        humidity = data['main']['humidity']
        weather_emoji = "☀️" if "clear" in description else "☁️" if "cloud" in description else "🌧️"
        wind_emoji = "💨"
        humidity_emoji = "💧"
        return (f"Погода в {city}: {weather_emoji}\n"
                f"Описание: {description}\n"
                f"Температура: {temp}°C\n"
                f"{wind_emoji} Скорость ветра: {wind_speed} м/с\n"
                f"{humidity_emoji} Влажность: {humidity}%")
    else:
        return None

@dp.message(Command('start'))
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Введите название города, чтобы узнать погоду:")
    await state.set_state(WeatherStates.city)

@dp.message(WeatherStates.city)
async def handle_city(message: Message, state: FSMContext):
    city = message.text
    weather = get_weather(city)
    
    if weather:
        await state.update_data(city=city)
        await message.answer(f"Город подтвержден: {city}\nВыберите, как часто присылать погоду:",
                             reply_markup=get_frequency_keyboard())
        await state.set_state(WeatherStates.frequency)
    else:
        await message.answer("Город не найден, попробуйте ввести другой город:")

def get_frequency_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Каждую минуту")
    builder.button(text="Каждый час")
    builder.button(text="Каждые 3 часа")
    builder.button(text="Каждый день")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


@dp.message(WeatherStates.frequency)
async def handle_frequency(message: Message, state: FSMContext):
    frequency = message.text
    user_data = await state.get_data()
    city = user_data.get('city')
    
    if frequency == "Каждую минуту":
        interval = 60
    elif frequency == "Каждый час":
        interval = 3600
    elif frequency == "Каждые 3 часа":
        interval = 10800
    elif frequency == "Каждый день":
        interval = 86400
    else:
        await message.answer("Пожалуйста, выберите частоту из предложенных на клавиатуре вариантов.")
        return

    await message.answer(f"Вы выбрали получать прогноз погоды для города {city} {frequency.lower()}.")
    

    asyncio.create_task(send_weather_updates(message.chat.id, city, interval))
    await state.clear()

async def send_weather_updates(chat_id, city, interval):
    while True:
        weather = get_weather(city)
        if weather:
            await bot.send_message(chat_id, weather)
        await asyncio.sleep(interval)

if __name__ == '__main__':
    dp.run_polling(bot)