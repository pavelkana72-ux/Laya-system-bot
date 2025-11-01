import os
import telebot
from flask import Flask
from supabase import create_client

# Берём токен из переменных окружения (именно так, как у тебя в Render)
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Диагностика при старте — чтобы в логах было видно причину, если чего нет
if not BOT_TOKEN:
    # Падать — плохо; выбрасываем явную ошибку с подсказкой
    raise RuntimeError("❌ TELEGRAM_TOKEN не найден. Проверь Environment Variables в Render (имя переменной TELEGRAM_TOKEN).")

print("✅ TELEGRAM_TOKEN найден. Инициализируем бота...")

# Инициализация бота и Supabase
bot = telebot.TeleBot(BOT_TOKEN)
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized.")
    except Exception as e:
        print("⚠️ Ошибка инициализации Supabase:", e)
else:
    print("⚠️ SUPABASE_URL / SUPABASE_KEY не заданы — Supabase отключён.")

# Простой веб-путь, чтобы Render считал сервис живым
app = Flask(__name__)

@app.route("/")
def home():
    return "🌿 Laya System is alive."

# Команды бота
@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.reply_to(message, "🌞 Привет. Я — Laya System. Пространство дыхания и пробуждения.")

@bot.message_handler(commands=["ping"])
def cmd_ping(message):
    bot.reply_to(message, "💫 pong — я жив.")

@bot.message_handler(func=lambda m: True)
def echo(message):
    # минимальная логика — отвечаем коротко
    bot.reply_to(message, "💫 Всё, что тебе нужно, уже внутри.")

# Запуск: бот в отдельном потоке + Flask главный процесс (Render требует прослушивания порта)
if __name__ == "__main__":
    import threading

    def run_bot():
        print("🚀 Запуск Telegram polling...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)

    t = threading.Thread(target=run_bot, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Запуск веб-сервера на портe {port}")
    app.run(host="0.0.0.0", port=port)
