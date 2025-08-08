import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
from bot_logic import register_handlers  # подключаем хендлеры из bot_logic.py

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise ValueError("Не указан TELEGRAM_TOKEN в переменных окружения Render")

app = FastAPI()

# Создаем приложение Telegram
telegram_app = Application.builder().token(TOKEN).build()
register_handlers(telegram_app)  # подключаем все хендлеры

@app.on_event("startup")
async def on_startup():
    """Устанавливаем вебхук при запуске на Render."""
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/telegram/webhook")
    print(f"Webhook установлен -> {WEBHOOK_URL}/telegram/webhook")

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Обработка апдейтов от Telegram через вебхук."""
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.initialize()
    await telegram_app.process_update(update)
    return {"ok": True}

@app.get("/")
async def root():
    """Проверка, что сервер запущен."""
    return {"status": "бот работает"}