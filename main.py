import os
import telebot
from flask import Flask
import threading

# Загружаем токен
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Проверим токен (для диагностики)
if not BOT_TOKEN:
    print("❌ Ошибка: TELEGRAM_TOKEN не найден! Проверь Environment Variables в Render.")
else:
    print("✅ TELEGRAM_TOKEN найден.")

# Создаем Flask сервер
app = Flask(__name__)

@app.route('/')
def home():
    return "🌿 Laya System Bot is active."

# Запуск бота
def start_bot():
    if not BOT_TOKEN:
        print("❌ Невозможно запустить бота — токен отсутствует.")
        return
    bot = telebot.TeleBot(BOT_TOKEN)

    @bot.message_handler(commands=['start'])
    def start_message(message):
        bot.reply_to(message, "Привет, я Laya System 🌬")

    bot.polling(non_stop=True)

# Основной запуск
if __name__ == "__main__":
    # Запускаем телеграм-бота в отдельном потоке
    threading.Thread(target=start_bot).start()

    # Flask слушает порт (Render подставляет автоматически)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
