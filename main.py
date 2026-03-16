import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import os
from aiohttp import web

# Настройки
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Домен от Render (будет виден после деплоя)
WEBHOOK_DOMAIN = "https://fokuzz-bot.onrender.com"
WEBHOOK_PATH = "/webhook"

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Привет! Я бот на webhook'ах. Конфликтов больше не будет!")

@dp.message()
async def handle_message(message: types.Message):
    await message.answer(f"Ты написал: {message.text}")

async def on_startup(bot: Bot):
    await bot.set_webhook(f"{WEBHOOK_DOMAIN}{WEBHOOK_PATH}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

async def main():
    # Запускаем aiohttp сервер
    app = web.Application()
    
    # Настраиваем webhook
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    # Добавляем health check для Render
    async def health_check(request):
        return web.Response(text="OK")
    app.router.add_get("/health", health_check)
    
    # Запускаем
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()
    logging.info("Webhook сервер запущен на порту 10000")
    
    # Держим сервер запущенным
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
