import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters

# 📦 Переменные окружения (указываются в Railway)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
ACTIVE_MODEL = DEFAULT_MODEL  # будет меняться через кнопки

# 🔘 Кнопки выбора модели
def model_selection_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("GPT-3.5", callback_data="gpt-3.5-turbo"),
            InlineKeyboardButton("GPT-4", callback_data="gpt-4"),
            InlineKeyboardButton("GPT-4o", callback_data="gpt-4o")
        ]
    ])

# 💱 Курс доллара через exchangerate.host
def get_usd_to_rub():
    try:
        response = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=RUB")
        rate = response.json()["rates"]["RUB"]
        return f"💵 Курс доллара: 1 USD = {rate:.2f} RUB"
    except Exception as e:
        return f"❌ Ошибка получения курса: {e}"

# 🧠 Ответ от GPT или курс
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()

    # 💬 Если запрос про курс доллара — отвечаем курсом
    if "курс доллара" in user_input or "доллар" in user_input:
        reply = get_usd_to_rub()
        await update.message.reply_text(reply, reply_markup=model_selection_keyboard())
        return

    # 🔁 Иначе — GPT-ответ
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

    await update.message.reply_text(reply, reply_markup=model_selection_keyboard())

# 🔘 Обработка кнопок выбора модели
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_MODEL
    query = update.callback_query
    await query.answer()

    selected_model = query.data
    allowed_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4o"]

    if selected_model in allowed_models:
        ACTIVE_MODEL = selected_model
        await query.edit_message_text(f"✅ Модель обновлена на: {ACTIVE_MODEL}")
    else:
        await query.edit_message_text("❌ Недопустимая модель.")

# 📍 Команда /model — показать текущую модель
async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🧠 Текущая модель: {ACTIVE_MODEL}")

# ▶️ Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
