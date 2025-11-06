from flask import Flask, request
import os
import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton
import random
import logging
import sys
from datetime import datetime, time
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import psycopg2
from psycopg2.extras import RealDictCursor

# ===== CONFIGURATION =====
TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
TIMEZONE = os.environ.get("TIMEZONE", "Europe/Moscow")
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not TOKEN or not DATABASE_URL:
    raise ValueError("❌ TELEGRAM_TOKEN и DATABASE_URL обязательны")

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

# ===== LOGGING =====
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# ===== DATABASE FUNCTIONS =====
def get_connection():
    try:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    except Exception as e:
        logger.error(f"DB connection error: {e}")
        raise

def init_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Users table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                chat_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                reminders_enabled BOOLEAN DEFAULT FALSE,
                last_action TEXT,
                last_active TIMESTAMP WITH TIME ZONE,
                practice_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # User practices
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user_practices (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT REFERENCES users(chat_id),
                practice_type TEXT NOT NULL,
                practice_name TEXT NOT NULL,
                duration_minutes INTEGER,
                completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')
        # Reminders
        cur.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT REFERENCES users(chat_id),
                reminder_time TIME,
                reminder_days TEXT,
                reminder_type TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        logger.info("DB initialized successfully")
    except Exception as e:
        logger.error(f"DB init error: {e}")

# ===== USER & PRACTICE FUNCTIONS =====
def get_user(chat_id, update_data=None):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE chat_id=%s", (chat_id,))
        user = cur.fetchone()
        if not user:
            if update_data:
                cur.execute('''
                    INSERT INTO users (chat_id, username, first_name, last_name, joined_at, last_active)
                    VALUES (%s,%s,%s,%s,%s,%s) RETURNING *
                ''', (
                    chat_id,
                    update_data.get('username'),
                    update_data.get('first_name'),
                    update_data.get('last_name'),
                    datetime.now(),
                    datetime.now()
                ))
            else:
                cur.execute('''
                    INSERT INTO users (chat_id, joined_at, last_active)
                    VALUES (%s,%s,%s) RETURNING *
                ''', (chat_id, datetime.now(), datetime.now()))
            user = cur.fetchone()
            conn.commit()
        else:
            cur.execute('''
                UPDATE users SET last_active=%s, updated_at=%s WHERE chat_id=%s
            ''', (datetime.now(), datetime.now(), chat_id))
            conn.commit()
        return user
    except Exception as e:
        logger.error(f"Error in get_user: {e}")
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()

def update_user(chat_id, updates):
    conn = get_connection()
    cur = conn.cursor()
    try:
        set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [datetime.now(), chat_id]
        cur.execute(f'''
            UPDATE users SET {set_clause}, updated_at=%s WHERE chat_id=%s
        ''', values)
        conn.commit()
    except Exception as e:
        logger.error(f"Error updating user {chat_id}: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def log_practice(chat_id, practice_type, practice_name, duration_minutes=None, notes=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO user_practices (chat_id, practice_type, practice_name, duration_minutes, notes)
            VALUES (%s,%s,%s,%s,%s)
        ''', (chat_id, practice_type, practice_name, duration_minutes, notes))
        cur.execute('''
            UPDATE users SET practice_count=practice_count+1, updated_at=%s WHERE chat_id=%s
        ''', (datetime.now(), chat_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging practice: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def get_user_stats(chat_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE chat_id=%s", (chat_id,))
        user = cur.fetchone()
        if not user:
            return None
        cur.execute('''
            SELECT 
                COUNT(*) as total_practices,
                COUNT(DISTINCT DATE(completed_at)) as practice_days,
                AVG(duration_minutes) as avg_duration,
                MAX(completed_at) as last_practice
            FROM user_practices WHERE chat_id=%s
        ''', (chat_id,))
        stats = cur.fetchone()
        cur.execute('''
            SELECT practice_name, COUNT(*) as count
            FROM user_practices
            WHERE chat_id=%s
            GROUP BY practice_name
            ORDER BY count DESC
            LIMIT 1
        ''', (chat_id,))
        favorite = cur.fetchone()
        return {'user': user, 'stats': stats, 'favorite_practice': favorite}
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return None
    finally:
        cur.close()
        conn.close()

# ===== PRACTICES =====
PRACTICES = {
    "meditation": {
        "name": "🧘 Медитация для начинающих",
        "description": "Базовая практика осознанности",
        "steps": [
            "Сядьте в удобное положение с прямой спиной",
            "Закройте глаза и сделайте 3 глубоких вдоха",
            "Сосредоточьтесь на дыхании",
            "Если ум отвлекается, мягко возвращайте внимание к дыханию",
            "Практикуйте 5-10 минут"
        ],
        "duration": "10 минут",
        "audio_url": "",
        "duration_minutes": 10
    },
    "morning_yoga": {
        "name": "🌅 Утренний комплекс йоги",
        "description": "Энергизирующая практика на утро",
        "steps": [
            "Сурья Намаскар - 5 кругов",
            "Поза Горы - 1 минута",
            "Поза Воина I - 30 сек на каждую сторону",
            "Поза Дерева - 1 минута на каждую сторону",
            "Наклон вперёд - 1 минута",
            "Шавасана - 3 минуты"
        ],
        "duration": "15 минут",
        "audio_url": "",
        "duration_minutes": 15
    },
    "breathing": {
        "name": "💨 Дыхательное упражнение",
        "description": "Балансирующее дыхание",
        "steps": [
            "Сядьте удобно, закройте глаза",
            "Правая рука: большой палец на правую ноздрю",
            "Закройте правую ноздрю, вдох через левую",
            "Закройте левую, откройте правую, выдох",
            "Повторите 10-15 циклов"
        ],
        "duration": "5 минут",
        "audio_url": "",
        "duration_minutes": 5
    }
}

# ===== KEYBOARDS =====
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🎯 Начать практику"), KeyboardButton("📊 Моя статистика")],
    [KeyboardButton("💫 Случайная цитата"), KeyboardButton("⏰ Напомнить о практике")],
    [KeyboardButton("ℹ️ О боте")]
], resize_keyboard=True)

practice_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🧘 Медитация"), KeyboardButton("🌅 Утренняя йога")],
    [KeyboardButton("💨 Дыхание"), KeyboardButton("📋 Все практики")],
    [KeyboardButton("🔙 Назад")]
], resize_keyboard=True)

# ===== QUOTES =====
MEDITATION_QUOTES = [
    "«Ты — небо. Все остальное — это просто погода.» — Пема Чодрон",
    "«Медитация — это не о том, чтобы избавиться от мыслей, а о том, чтобы наблюдать их без осуждения.»",
    "«Самый важный момент для медитации — сейчас.»",
    "«В тишине ума рождается мудрость.» — Шри Юктешвар",
    "«Практика медитации — это подарок, который вы делаете себе каждый день.»"
]

# ===== SCHEDULER =====
scheduler = BackgroundScheduler(timezone=pytz.timezone(TIMEZONE))

def send_daily_reminder():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM users WHERE reminders_enabled=TRUE")
        users = cur.fetchall()
        for (chat_id,) in users:
            try:
                safe_send_message(chat_id, "🌅 Доброе утро! Время для практики 🎯", parse_mode='Markdown')
            except:
                continue
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error in daily reminder: {e}")

scheduler.add_job(send_daily_reminder, trigger=CronTrigger(hour=8, minute=0), id='daily_reminder')

# ===== HELPER FUNCTIONS =====
def safe_send_message(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except telegram.error.TelegramError as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")
        return None

def log_user_action(chat_id, action):
    update_user(chat_id, {'last_action': action})
