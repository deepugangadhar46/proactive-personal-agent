import sqlite3
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters
from datetime import datetime
from datetime import time
from dotenv import load_dotenv
from flask import Flask
from flask import request as flask_request
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")



# ---------- DATABASE SETUP ----------
conn = sqlite3.connect("tasks.db", check_same_thread=False)
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


# ---------- COMMANDS ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print("Your Chat ID:", chat_id)

    await update.message.reply_text(
        "Personal AI Agent v0.2 🚀\n\n"
        "Proactive mode loading..."
    )


    
async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)

    if not text:
        await update.message.reply_text("Usage: /addtask Task name | YYYY-MM-DD")
        return

    if "|" in text:
        task, deadline = map(str.strip, text.split("|"))
    else:
        task = text
        deadline = None

    cursor.execute(
        "INSERT INTO tasks (task, deadline, status) VALUES (?, ?, ?)",
        (task, deadline, "pending")
    )
    conn.commit()

    await update.message.reply_text(f"✅ Task added: {task}")

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM tasks WHERE status='pending'")
    tasks = cursor.fetchall()

    if not tasks:
        await update.message.reply_text("No pending tasks 🎉")
        return

    message = "Your Pending Tasks:\n\n"

    for task in tasks:
        deadline_info = f" (Due: {task[2]})" if task[2] else ""
        message += f"{task[0]}. {task[1]}{deadline_info}\n"

    await update.message.reply_text(message)

async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /done <task_id>")
        return

    task_id = context.args[0]

    cursor.execute("UPDATE tasks SET status='done' WHERE id=?", (task_id,))
    conn.commit()

    await update.message.reply_text(f"✅ Task {task_id} marked as done!")

CHAT_ID = 1265910148

async def daily_checkin(context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM tasks WHERE status='pending'")
    tasks = cursor.fetchall()

    if not tasks:
        message = "🎉 You have no pending tasks. Good job!"
    else:
        message = "👋 Daily Check-in\n\nYou still have:\n\n"
        for task in tasks:
            message += f"{task[0]}. {task[1]}\n"
        message += "\nDid you complete any of them?"

    await context.bot.send_message(chat_id=CHAT_ID, text=message)

async def natural_language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "tomorrow" in text:
        from datetime import datetime, timedelta
        deadline = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        deadline = None

    if "i need to" in text or "i have to" in text:
        task = text.replace("i need to", "").replace("i have to", "").strip()

        cursor.execute(
            "INSERT INTO tasks (task, deadline, status) VALUES (?, ?, ?)",
            (task, deadline, "pending")
        )
        conn.commit()

        await update.message.reply_text(f"✅ Got it. Added task: {task}")

# ---------- WEBHOOK APP ----------

flask_app = Flask(__name__)

PORT = int(os.environ.get("PORT", 10000))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addtask", add_task))
app.add_handler(CommandHandler("tasks", show_tasks))
app.add_handler(CommandHandler("done", mark_done))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, natural_language_handler))

app.job_queue.run_daily(
    daily_checkin,
    time=time(hour=20, minute=0)
)


@flask_app.post(f"/{TOKEN}")
async def webhook():
    update = Update.de_json(flask_request.json, app.bot)
    await app.process_update(update)
    return "ok"


@flask_app.get("/")
def health():
    return "Bot is running"


async def setup_webhook():
    await app.initialize()
    await app.bot.set_webhook(url=f"{RENDER_EXTERNAL_URL.rstrip('/')}/{TOKEN}")


if __name__ == "__main__":
    if RENDER_EXTERNAL_URL:
        asyncio.run(setup_webhook())
        flask_app.run(host="0.0.0.0", port=PORT)
    else:
        print("RENDER_EXTERNAL_URL is not set; starting in polling mode.")
        app.run_polling()