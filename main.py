import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# 📦 Переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
ACTIVE_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# 💱 Получение курса валют и криптовалют в RUB и USD
def get_currency_rate_to_rub(query: str) -> str:
    fiat_aliases = {
        "доллар": "USD",
        "евро": "EUR",
        "фунт": "GBP",
        "иена": "JPY",
        "юань": "CNY",
        "франк": "CHF",
        "гривна": "UAH",
        "тенге": "KZT",
        "рупия": "INR"
    }

    crypto_aliases = {
        "биткоин": "bitcoin",
        "btc": "bitcoin",
        "эфир": "ethereum",
        "eth": "ethereum",
        "додж": "dogecoin",
        "doge": "dogecoin",
        "usdt": "tether",
        "тезер": "tether",
        "bnb": "binancecoin",
        "ripple": "ripple",
        "xrp": "ripple",
        "sol": "solana"
    }

    words = query.lower().split()

    # 🔸 Криптовалюты
    for word in words:
        crypto_id = crypto_aliases.get(word)
        if crypto_id:
            try:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=rub,usd"
                response = requests.get(url, timeout=5)
                data = response.json()

                if crypto_id in data:
                    rub = data[crypto_id].get("rub")
                    usd = data[crypto_id].get("usd")

                    if rub and usd:
                        return (
                            f"💰 Курс {crypto_id.capitalize()}:\n"
                            f"1 {crypto_id.upper()} = {rub:,.2f} RUB\n"
                            f"1 {crypto_id.upper()} = {usd:,.2f} USD"
                        )
                    else:
                        return f"⚠️ Не удалось получить оба курса для {crypto_id}."
                else:
                    return f"⚠️ Не удалось получить данные для {crypto_id}."
            except Exception as e:
                return f"❌ Ошибка получения курса криптовалюты: {e}"

    # 🔸 Фиатные валюты
    for word in words:
        fiat_code = fiat_aliases.get(word, word.upper())
        if len(fiat_code) == 3 and fiat_code.isalpha():
            try:
                url = f"https://open.er-api.com/v6/latest/{fiat_code}"
                response = requests.get(url, timeout=5)
                data = response.json()
                rates = data.get("rates", {})
                rub = rates.get("RUB")
                usd = rates.get("USD")

                if rub and usd:
                    return (
                        f"💱 Курс {fiat_code}:\n"
                        f"1 {fiat_code} = {rub:,.2f} RUB\n"
                        f"1 {fiat_code} = {usd:,.2f} USD"
                    )
                elif rub:
                    return f"💱 Курс {fiat_code}: 1 {fiat_code} = {rub:,.2f} RUB"
                else:
                    return f"⚠️ Курс RUB или USD для {fiat_code} не найден."
            except Exception as e:
                return f"❌ Ошибка получения курса: {e}"

    return "❓ Укажите валюту (например: курс доллар, курс BTC, курс ETH)"

# 🧠 Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()

    if "курс" in user_input:
        reply = get_currency_rate_to_rub(user_input)
        await update.message.reply_text(reply)
        return

    # 🔁 GPT-ответ через OpenAI API
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
