import telebot
import os
from flask import Flask
from supabase import create_client

# Загружаем переменные окружения
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Проверим, всё ли загружено
print("BOT_TOKEN:", bool(BOT_TOKEN))
print("SUPABASE_URL:", bool(SUPABASE_URL))
print("SUPABASE_KEY:", bool(SUPABASE_KEY))

# Создаём объекты
bot = telebot.TeleBot(BOT_TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
server = Flask(__name__)

# Обработчик Telegram-команд
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "🌿 Добро пожаловать в Laya System — пространство дыхания и пробуждения.")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    bot.reply_to(message, "💫 Всё, что тебе нужно, уже внутри.")

# Flask маршрут для Render
@server.route("/")
def home():
    return "Laya System Bot is alive."

if __name__ == "__main__":
    # Если Render запускает как веб-сервис
    import threading
    t = threading.Thread(target=lambda: bot.polling(none_stop=True, interval=1))
    t.start()
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
