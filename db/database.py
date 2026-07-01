import sqlite3

def get_connection():
    conn = sqlite3.connect("tasks.db", check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        deadline TEXT,
        status TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()