import os
import openai
import asyncio
import aiohttp
import schedule
import time
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import random

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POST_TIMES = os.getenv("POST_TIMES", "08:00,12:00,18:00,21:00").split(",")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

TOPICS = ["наука", "технологии", "история", "космос", "медицина", "психология", "искусство"]

async def generate_text():
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    prompt = (
        f"Придумай интересный, но малоизвестный факт на тему {random.choice(TOPICS)}. "
        "Пиши так, чтобы текст был естественным, без 'Факт:' в начале. "
        "Добавь лёгкий юмор, чтобы он звучал не как анекдот, а как забавное наблюдение. "
        "Избегай канцелярита, сложных оборотов и очевидных шуток."
    )
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                text = data.get("choices")[0]["message"]["content"] if "choices" in data else None
                print(f"📝 Сгенерированный текст: {text}")
                return text
            else:
                print(f"❌ Ошибка при генерации текста: {await response.text()}")
                return None

async def generate_image(prompt):
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {"model": "dall-e-3", "prompt": prompt, "size": "1024x1024"}
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/images/generations", json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if "data" in data:
                    image_url = data["data"][0]["url"]
                    print(f"🖼️ Сгенерированное изображение: {image_url}")
                    return image_url
            print(f"❌ Ошибка генерации изображения: {await response.text()}")
            return None

async def create_post():
    fact_text = await generate_text()
    if not fact_text:
        print("❌ Не удалось сгенерировать текст")
        return

    image_url = await generate_image(fact_text)
    if not image_url:
        image_url = await generate_image("Интересный научный факт, инфографика, минимализм, яркие цвета.")

    try:
        if image_url:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=f"📝 {fact_text}")
            print(f"✅ Пост опубликован: {fact_text}")
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=f"📝 {fact_text}\n⚠️ Без изображения")
            print(f"⚠️ Пост опубликован без изображения: {fact_text}")
    except Exception as e:
        print(f"❌ Ошибка при публикации: {e}")

def schedule_posts():
    for post_time in POST_TIMES:
        schedule.every().day.at(post_time.strip()).do(lambda: asyncio.run(create_post()))

def run_scheduler():
    schedule_posts()
    print("📅 Бот запущен и будет публиковать посты в указанное время.")
    while True:
        schedule.run_pending()
        time.sleep(30)  # Проверяем каждые 30 секунд

if __name__ == "__main__":
    run_scheduler()
