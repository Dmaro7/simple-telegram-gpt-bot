import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# 📦 Переменные окружения (Railway)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
ACTIVE_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # можно задать gpt-3.5-turbo или gpt-4

# 💱 Функция для получения курса доллара
def get_usd_to_rub():
    try:
        response = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=RUB", timeout=5)
        data = response.json()

        # Проверяем структуру
        if "rates" in data and "RUB" in data["rates"]:
            rate = data["rates"]["RUB"]
            return f"💵 Курс доллара: 1 USD = {rate:.2f} RUB"
        else:
            return "⚠️ Не удалось получить актуальный курс. Попробуйте позже."
    except Exception as e:
        return f"❌ Ошибка получения курса: {e}"

# 💬 Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()

    # 💱 Если запрос касается курса доллара
    if "курс доллара" in user_input or "доллар" in user_input:
        reply = get_usd_to_rub()
        await update.message.reply_text(reply)
        return

    # 🔁 GPT-ответ
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
        reply = f"(Модель: {model_used})\n\n{reply_text}"
    except Exception as e:
        reply = f"❌ Ошибка: {str(e)}"

    await update.message.reply_text(reply)

# 🧠 Команда /model — вывод текущей модели
async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🧠 Текущая модель: {ACTIVE_MODEL}")

# ▶️ Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("model", model_command))
    app.run_polling()
