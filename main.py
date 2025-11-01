import telebot
from telebot import types
from supabase import create_client, Client
import os

# Загружаем переменные окружения (Render уже хранит их)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Создаём клиента Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Создаём бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Проверяем соединение с Supabase при запуске
try:
    response = supabase.table("users").select("*").limit(1).execute()
    print("✅ Supabase подключён успешно!")
except Exception as e:
    print("⚠️ Ошибка подключения к Supabase:", e)


# --- Главное меню ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🕉 Утро")
    btn2 = types.KeyboardButton("☀️ День")
    btn3 = types.KeyboardButton("🌙 Вечер")
    btn4 = types.KeyboardButton("🌌 Ночь")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    return markup


# --- Команды и логика ---
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    user_name = message.from_user.first_name

    # Добавляем пользователя в базу, если его нет
    try:
        supabase.table("users").insert({"id": user_id, "name": user_name}).execute()
    except Exception as e:
        print("⚠️ Ошибка добавления пользователя:", e)

    bot.send_message(
        user_id,
        "Добро пожаловать в Laya System 🌿\nВыбери состояние:",
        reply_markup=main_menu(),
    )


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "🕉 Утро":
        bot.send_message(message.chat.id, "Практика утреннего дыхания:\n\nВдох — 4, задержка — 2, выдох — 6.")
    elif message.text == "☀️ День":
        bot.send_message(message.chat.id, "Практика на день:\n\nОщути ритм дыхания и движения. Всё уже происходит.")
    elif message.text == "🌙 Вечер":
        bot.send_message(message.chat.id, "Практика вечернего расслабления:\n\nВыдохни через рот. Позволь телу отдохнуть.")
    elif message.text == "🌌 Ночь":
        bot.send_message(message.chat.id, "Ночная медитация:\n\nЗакрой глаза. Всё растворяется в покое.")
    else:
        bot.send_message(message.chat.id, "Выбери состояние из меню 🌿", reply_markup=main_menu())


# --- Запуск бота ---
if __name__ == "__main__":
    bot.polling(none_stop=True)
