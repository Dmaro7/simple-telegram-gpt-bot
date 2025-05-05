import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# 📦 Переменные окружения (Railway)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
ACTIVE_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # Можно: gpt-3.5-turbo, gpt-4, gpt-4o

# 💱 Получение курса валюты к RUB через Frankfurter API
def get_currency_rate_to_rub(query: str) -> str:
    aliases = {
        "доллар": "USD",
        "евро": "EUR",
        "фунт": "GBP",
        "иена": "JPY",
        "юань": "CNY",
        "юани": "CNY",
        "франк": "CHF",
        "гривна": "UAH",
        "тенге": "KZT",
        "рупия": "INR"
    }

    for word in query.split():
        code = aliases.get(word.lower(), word.upper())
        if len(code) == 3 and code.isalpha():
            try:
                url = f"https://api.frankfurter.app/latest?from={code}&to=RUB"
                response = requests.get(url, timeout=5)
                data = response.json()

                if "rates" in data and "RUB" in data["rates"]:
                    rate = data["rates"]["RUB"]
                    return f"💱 Курс {code}: 1 {code} = {rate:.2f} RUB"
                else:
                    return f"⚠️ Frankfurter API не вернул курс RUB для {code}."
            except Exception as e:
                return f"❌ Ошибка получения курса: {e}"

    return "❓ Укажите валюту (например: курс доллар, курс EUR, курс фунта)"

# 💬 Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()

    if "курс" in user_input:
        reply = get_currency_rate_to_rub(user_input)
        await update.message.reply_text(reply)
        return

    # GPT-ответ
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

# 📍 Команда /model — текущая модель
async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🧠 Текущая модель: {ACTIVE_MODEL}")

# ▶️ Запуск Telegram-бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("model", model_command))
    app.run_polling()
