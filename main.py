import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# Переменные окружения (настраиваются в Railway)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Глобальная модель (можно менять через /model)
ACTIVE_MODEL = DEFAULT_MODEL

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Project": PROJECT_ID,
        "Content-Type": "application/json"
    }

    data = {
        "model": ACTIVE_MODEL,
        "messages": [{"role": "user", "content": user_input}]
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        response_data = response.json()
        model_used = response_data.get("model", "неизвестно")
        reply_text = response_data["choices"][0]["message"]["content"]
        reply = f"(GPT: {model_used})\n\n{reply_text}"
    except Exception as e:
        reply = f"❌ Ошибка: {str(e)}"

    await update.message.reply_text(reply)

# Команда /model для просмотра и изменения модели
async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_MODEL

    allowed_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4o"]

    if context.args:
        requested_model = context.args[0]
        if requested_model in allowed_models:
            ACTIVE_MODEL = requested_model
            await update.message.reply_text(f"✅ Модель обновлена на: {ACTIVE_MODEL}")
        else:
            await update.message.reply_text(
                f"❌ Модель недопустима.\nДопустимые варианты: {', '.join(allowed_models)}"
            )
    else:
        await update.message.reply_text(f"🧠 Текущая модель: {ACTIVE_MODEL}")

# Запуск Telegram-бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("model", model_command))
    app.run_polling()
