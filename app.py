import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder

TOKEN = os.environ["TELEGRAM_TOKEN"]
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

app = FastAPI()

# Создаём приложение бота
application = ApplicationBuilder().token(TOKEN).build()

# Подключаем логику из bot_logic.py
from bot_logic import register_handlers
register_handlers(application)


@app.get("/")
async def root():
    return {"ok": True}


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    if WEBHOOK_SECRET:
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if secret != WEBHOOK_SECRET:
            return {"ok": False}
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


@app.on_event("startup")
async def on_startup():
    # Обязательная инициализация бота для PTB 21.x
    await application.initialize()
    await application.start()

    if not WEBHOOK_URL:
        print("WEBHOOK_URL не задан — пропускаю setWebhook")
        return

    await application.bot.set_webhook(
        url=f"{WEBHOOK_URL}/telegram/webhook",
        secret_token=WEBHOOK_SECRET or None,
        drop_pending_updates=True,
    )
    print("Webhook set ->", f"{WEBHOOK_URL}/telegram/webhook")


@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()