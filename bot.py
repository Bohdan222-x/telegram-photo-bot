import os
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime, timedelta

# 🔐 Токен
TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [1260925293, 7000360153, 5019338211, 8202200069, 7635142772, 7809303196]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ===== РОБОТА З БАЗОЮ ДАНИХ =====
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS cooldowns 
                      (user_id INTEGER PRIMARY KEY, last_time TEXT)''')
    conn.commit()
    conn.close()

def get_last_time(user_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT last_time FROM cooldowns WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    if res:
        return datetime.strptime(res[0], "%Y-%m-%d %H:%M:%S")
    return None

def set_last_time(user_id, time_now):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    time_str = time_now.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR REPLACE INTO cooldowns (user_id, last_time) VALUES (?, ?)", (user_id, time_str))
    conn.commit()
    conn.close()

# ===== ЛОГІВАННЯ =====
def log(text):
    print(f"[{datetime.now()}] {text}") # На Koyeb краще дивитись у консоль

PHOTO_COOLDOWN = timedelta(hours=15)

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Приветствую 👋\nКидай свою фотографию 📸")

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    now = datetime.now()
    
    last_time = get_last_time(user_id)

    if last_time:
        diff = now - last_time
        if diff < PHOTO_COOLDOWN:
            remaining = PHOTO_COOLDOWN - diff
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            await message.answer(f"⏳ Ты уже отправлял фото\nПопробуй через {hours} ч {minutes} мин")
            return

    photo = message.photo[-1].file_id
    username = message.from_user.username or "без username"
    caption = f"📸 Новое фото\nОт: @{username}\nID: {user_id}"

    for admin_id in ADMINS:
        try:
            await bot.send_photo(chat_id=admin_id, photo=photo, caption=caption)
        except Exception as e:
            log(f"❌ Помилка адмін {admin_id}: {e}")

    set_last_time(user_id, now)
    await message.answer("✅ Фото отправилось на рассмотрение")

if __name__ == "__main__":
    init_db()
    executor.start_polling(dp, skip_updates=True)
