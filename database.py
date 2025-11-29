import sqlite3
DB_PATH = "data.db"

def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS startups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT, stage TEXT, description TEXT, rating REAL DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, date TEXT, location TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS subscriptions (user_id INTEGER NOT NULL, startup_id INTEGER NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS user_state (user_id INTEGER PRIMARY KEY, filter_category TEXT, filter_stage TEXT)")
    db.commit()
    db.close()
