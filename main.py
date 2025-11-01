import telebot
import os
from supabase import create_client

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "🌿 Добро пожаловать в Laya System — пространство дыхания и пробуждения.")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    bot.reply_to(message, "💫 Всё, что тебе нужно, уже внутри.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
