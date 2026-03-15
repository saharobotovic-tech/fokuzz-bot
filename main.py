import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os
from aiohttp import web
from openai import OpenAI

# Настройки
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Клиент OpenRouter
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Простой HTTP-сервер для Render
async def handle_health(request):
    return web.Response(text="OK")

async def run_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()
    logging.info("Health check server started on port 10000")

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Привет! Я бот, работающий через нейросеть. Отправь мне фото или текст.")

@dp.message()
async def handle_message(message: types.Message):
    try:
        # Здесь будет логика с OpenRouter
        user_text = message.text or "Без текста"
        
        # Если есть фото
        if message.photo:
            await message.answer("Фото получено! Обработка через LLM скоро будет...")
        else:
            # Простой ответ через OpenRouter
            completion = client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=[{"role": "user", "content": user_text}]
            )
            response = completion.choices[0].message.content
            await message.answer(response)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("Произошла ошибка при обработке запроса. Попробуйте позже.")

async def main():
    # Запускаем HTTP-сервер для Render
    asyncio.create_task(run_web_server())
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
