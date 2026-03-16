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

# Проверка наличия ключей
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден!")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY не найден!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
        # Проверяем, есть ли текст
        if not message.text:
            await message.answer("Пожалуйста, отправь текстовое сообщение.")
            return
            
        user_text = message.text
        logging.info(f"Получено сообщение: {user_text[:50]}...")
        
        # Если есть фото
        if message.photo:
            await message.answer("Фото получено! Обработка через LLM скоро будет...")
            # Здесь потом добавим обработку фото
            return
        
        # Отправляем в OpenRouter
        try:
            completion = client.chat.completions.create(
                model="google/gemini-2.0-flash-exp:free",
                messages=[{"role": "user", "content": user_text}],
                timeout=30
            )
            response = completion.choices[0].message.content
            await message.answer(response)
            logging.info("Ответ успешно отправлен")
            
        except Exception as e:
            logging.error(f"Ошибка OpenRouter: {str(e)}")
            await message.answer("Ошибка при обращении к нейросети. Попробуй позже.")
            
    except Exception as e:
        logging.error(f"Необработанная ошибка: {str(e)}", exc_info=True)
        await message.answer("Произошла ошибка при обработке запроса. Попробуйте позже.")

async def main():
    # Сбрасываем вебхук и удаляем все ожидающие обновления (убивает конфликт)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем HTTP-сервер для Render
    asyncio.create_task(run_web_server())
    
    # Запускаем бота
    logging.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
