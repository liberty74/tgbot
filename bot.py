import telebot
import random
from google import genai
from telebot import types
from google.genai import types as genai_types

try:
    from database import get_db, init_db
except ImportError:
    print("ОШИБКА: Файл database.py не найден. Убедись, что он существует.")
    def init_db(): pass
    def get_db(): return None

TELEGRAM_TOKEN = "8068367316:AAGr4-ssDhDaVvzfEulOArWjuFrXRHanQ9A" 
GOOGLE_API_KEY = "AIzaSyDy0oQ3_VBQYi0U_iMQ4Z2eI2fPbxQae9I"

SYSTEM_PROMPT = """
Ты — ИИ-помощник бота Aqmola Start.
Твоя задача: помогать пользователю находить стартапы, специалистов, команды и события региона.
Отвечай кратко, по делу, без воды.
Понимай запросы (поиск, рекомендации, вопросы об экосистеме) и направляй к нужной информации.
Не выдумывай данные — если нет информации, говори об этом и предлагай ближайшие варианты.

ВАЖНО:
1. Не используй смайлики (эмодзи).
2. Не используй Markdown-форматирование (жирный шрифт, курсив и т.д.).
3. Пиши только простой текст.
"""

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GOOGLE_API_KEY)

init_db()

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id,
        "Привет. Я Aqmola Start AI.\n\n"
        "Чем могу помочь по экосистеме региона?\n"
        "Спроси меня о стартапах, событиях или командах.\n\n"
        "Меню команд:\n"
        "/startups — Список стартапов\n"
        "/search <имя> — Поиск\n"
        "/filter <категория> <этап> — Фильтр\n"
        "/events — События\n"
        "/add_startup — Добавить проект\n"
    )

@bot.message_handler(commands=["startups"])
def startups(message):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT id, name, category, stage FROM startups")
    rows = c.fetchall()
    db.close()
    if not rows:
        bot.send_message(message.chat.id, "В базе пока нет стартапов.")
        return
    text = "Список стартапов:\n\n"
    for r in rows:
        text += f"{r[1]}\nКатегория: {r[2]}\nЭтап: {r[3]}\n\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["search"])
def search(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Напиши: /search <название>")
        return
    q = parts[1]
    db = get_db()
    c = db.cursor()
    c.execute("SELECT id, name, description FROM startups WHERE name LIKE ?", ('%'+q+'%',))
    rows = c.fetchall()
    db.close()
    if not rows:
        bot.send_message(message.chat.id, "Ничего не найдено.")
        return
    text = ""
    for r in rows:
        text += f"{r[1]}\n{r[2]}\n\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["random"])
def random_cmd(message):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT id, name, category, stage FROM startups")
    rows = c.fetchall()
    db.close()
    if not rows:
        bot.send_message(message.chat.id, "База пуста.")
        return
    r = random.choice(rows)
    bot.send_message(message.chat.id, f"{r[1]}\nКатегория: {r[2]}\nЭтап: {r[3]}")

@bot.message_handler(commands=["top"])
def top(message):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT name, rating FROM startups ORDER BY rating DESC LIMIT 5")
    rows = c.fetchall()
    db.close()
    if not rows:
        bot.send_message(message.chat.id, "Нет данных для рейтинга.")
        return
    text = "Топ стартапов:\n"
    for i, r in enumerate(rows, start=1):
        text += f"{i}. {r[0]} — {r[1]}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["events"])
def events(message):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT title, date, location FROM events ORDER BY date")
    rows = c.fetchall()
    db.close()
    if not rows:
        bot.send_message(message.chat.id, "Предстоящих событий нет.")
        return
    text = "События:\n\n"
    for r in rows:
        text += f"{r[0]}\n{r[1]}\n{r[2]}\n\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["filter"])
def filter_cmd(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, "Пример: /filter IT MVP")
        return
    cat = parts[1]
    stage = parts[2]
    uid = message.from_user.id
    db = get_db()
    c = db.cursor()
    c.execute("REPLACE INTO user_state (user_id, filter_category, filter_stage) VALUES (?, ?, ?)", (uid, cat, stage))
    db.commit()
    db.close()
    bot.send_message(message.chat.id, f"Фильтр установлен: {cat}, {stage}")

@bot.message_handler(commands=["subscribe"])
def subscribe(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Пример: /subscribe 1")
        return
    uid = message.from_user.id
    try:
        sid = int(parts[1])
        db = get_db()
        c = db.cursor()
        c.execute("INSERT INTO subscriptions (user_id, startup_id) VALUES (?, ?)", (uid, sid))
        db.commit()
        db.close()
        bot.send_message(message.chat.id, "Подписка оформлена.")
    except Exception:
        bot.send_message(message.chat.id, "Ошибка. Проверь ID.")

@bot.message_handler(commands=["add_startup"])
def add_startup(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.send_message(message.chat.id, "Пример: /add_startup ProjectName IT")
        return
    name = parts[1]
    category = parts[2]
    db = get_db()
    c = db.cursor()
    c.execute("INSERT INTO startups (name, category, stage, rating, description) VALUES (?, ?, ?, ?, ?)",
              (name, category, "MVP", 0, "Описание отсутствует"))
    db.commit()
    db.close()
    bot.send_message(message.chat.id, f"Стартап {name} добавлен.")

@bot.message_handler(commands=["add_event"])
def add_event(message):
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        bot.send_message(message.chat.id, "Пример: /add_event Hackathon 2025-10-10 Astana")
        return
    title = parts[1]
    date = parts[2]
    location = parts[3]
    db = get_db()
    c = db.cursor()
    c.execute("INSERT INTO events (title, date, location) VALUES (?, ?, ?)",
              (title, date, location))
    db.commit()
    db.close()
    bot.send_message(message.chat.id, f"Событие {title} добавлено.")

@bot.message_handler(content_types=['text'])
def handle_ai_chat(message):
    user_text = message.text
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )
        bot.reply_to(message, response.text)

    except Exception as e:
        print(f"Ошибка API: {e}")
        bot.reply_to(message, "Ошибка обработки запроса. Попробуй позже.")

if __name__ == '__main__':
    print("Бот Aqmola Start запущен...")
    bot.infinity_polling()