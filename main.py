import telebot
from telebot import types
from supabase import create_client, Client
import os
from datetime import datetime

# === Настройки окружения ===
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Главная клавиатура ===
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🌞 Практика дня", "🌬 Дыхание")
    markup.row("🧘 Профиль", "⚙️ Настройки")
    return markup

# === Старт ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Без имени"

    # Проверяем, есть ли пользователь
    data, _ = supabase.table("users").select("*").eq("telegram_id", user_id).execute()
    if not data:
        supabase.table("users").insert({
            "telegram_id": user_id,
            "username": username,
            "state": "idle",
            "created_at": datetime.now().isoformat()
        }).execute()

    bot.send_message(
        message.chat.id,
        f"Привет, {username} 🌿\nЯ — Laya. Твоя дыхательная система готова.",
        reply_markup=main_menu()
    )

# === Обработка кнопок ===
@bot.message_handler(func=lambda msg: True)
def handle_buttons(message):
    text = message.text

    if text == "🌞 Практика дня":
        send_practice(message)
    elif text == "🌬 Дыхание":
        send_breathing(message)
    elif text == "🧘 Профиль":
        show_profile(message)
    elif text == "⚙️ Настройки":
        bot.send_message(message.chat.id, "Настройки пока в разработке ⚙️")
    else:
        bot.send_message(message.chat.id, "Выбери действие из меню 👇", reply_markup=main_menu())

# === Практика дня ===
def send_practice(message):
    practices = [
        {
            "name": "Дыхание утреннего солнца",
            "description": "Сядь удобно. Вдох — свет наполняет тело. Выдох — отпусти всё старое. 5 циклов дыхания.",
            "duration": "3 минуты"
        },
        {
            "name": "Синхронизация сердца",
            "description": "Положи руку на сердце. Дыши ровно, считай до 4 на вдох и 4 на выдох. Почувствуй ритм жизни.",
            "duration": "5 минут"
        }
    ]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for p in practices:
        markup.add(p["name"])
    markup.add("⬅️ Назад")

    bot.send_message(message.chat.id, "Выбери практику:", reply_markup=markup)

# === Отображение профиля ===
def show_profile(message):
    user_id = message.from_user.id
    data, _ = supabase.table("users").select("*").eq("telegram_id", user_id).execute()
    if data:
        user = data[0]
        bot.send_message(
            message.chat.id,
            f"🧘 Профиль\nИмя: {user['username']}\nСостояние: {user['state']}",
            reply_markup=main_menu()
        )
    else:
        bot.send_message(message.chat.id, "Профиль не найден.", reply_markup=main_menu())

# === Запуск ===
if __name__ == "__main__":
    print("✨ Laya System запущена...")
    bot.polling(none_stop=True, timeout=60)
