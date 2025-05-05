import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()  # Работает и локально, Railway просто игнорирует .env

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # Можно задать в Railway

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Project": PROJECT_ID,
        "Content-Type": "application/json"
    }

    data = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": user_input}]
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
        else:
            reply = f"❌ Ошибка {response.status_code}: {response.json()['error']['message']}"
    except Exception as e:
        reply = f"⚠️ Ошибка при запросе: {str(e)}"

    await update.message.reply_text(reply)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
