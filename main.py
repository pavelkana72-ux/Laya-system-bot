import telebot
from telebot import types
from flask import Flask, request
import os
from supabase import create_client

# --- Supabase setup ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Telegram setup ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)
WEBHOOK_URL = "https://laya-system-bot.onrender.com/" + TOKEN

# --- Flask setup for Render ---
app = Flask(__name__)

# --- Основное меню ---
def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🕊 Утро: Пробуждение")
    btn2 = types.KeyboardButton("🌞 День: Поддержка")
    btn3 = types.KeyboardButton("🌙 Вечер: Интеграция")
    btn4 = types.KeyboardButton("🌌 Ночь: Восстановление")
    keyboard.add(btn1, btn2)
    keyboard.add(btn3, btn4)
    return keyboard

# --- Старт ---
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в Laya System.\n"
        "Выбери состояние, с которого начнём сегодня 🌿",
        reply_markup=main_keyboard()
    )

# --- Практики ---
@bot.message_handler(func=lambda msg: msg.text in [
    "🕊 Утро: Пробуждение", "🌞 День: Поддержка",
    "🌙 Вечер: Интеграция", "🌌 Ночь: Восстановление"
])
def send_practice(message):
    text = message.text

    if "Утро" in text:
        practice = "🕊 *Практика утреннего дыхания*\n\nМягко вдохни через нос, ощущая как тело просыпается.\nЗадержи дыхание на 2 секунды — и выдохни всё старое.\nПовтори 3 раза, ощущая внутренний свет."
    elif "День" in text:
        practice = "🌞 *Практика поддержки*\n\nСделай короткую паузу. Положи руку на грудь.\nСкажи себе: «Я здесь. Всё происходит правильно».\nСделай глубокий вдох и отпусти."
    elif "Вечер" in text:
        practice = "🌙 *Практика интеграции*\n\nСядь удобно. Почувствуй благодарность.\nЗакрой глаза и вспомни один момент, за который ты благодарен сегодня.\nПозволь этому чувству наполнить тебя."
    else:
        practice = "🌌 *Практика восстановления*\n\nЛяг, расслабь тело. Почувствуй вес.\nС каждым выдохом отпускай напряжение.\nВсё, что тебе не нужно — уходит.\nТы в безопасности."

    bot.send_message(message.chat.id, practice, parse_mode="Markdown")

# --- Flask routes ---
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Laya System Bot is alive", 200

# --- Webhook setup ---
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host='0.0.0.0', port=10000)
