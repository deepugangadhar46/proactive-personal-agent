import os
import sqlite3
import asyncio
from datetime import datetime, timedelta, time

from dotenv import load_dotenv
from flask import Flask, request

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==============================
# LOAD ENV
# ==============================

load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN not found in environment variables.")

# ==============================
# DATABASE SETUP
# ==============================

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

# ==============================
# COMMAND HANDLERS
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Proactive Personal Agent\n\n"
        "Commands:\n"
        "/addtask Task | YYYY-MM-DD\n"
        "/tasks\n"
        "/done <id>"
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
        (task, deadline, "pending"),
    )
    conn.commit()

    await update.message.reply_text(f"✅ Task added: {task}")


async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM tasks WHERE status='pending'")
    tasks = cursor.fetchall()

    if not tasks:
        await update.message.reply_text("🎉 No pending tasks.")
        return

    message = "📋 Pending Tasks:\n\n"
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


async def natural_language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    deadline = None
    if "tomorrow" in text:
        deadline = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    if "i need to" in text or "i have to" in text:
        task = (
            text.replace("i need to", "")
            .replace("i have to", "")
            .strip()
        )

        cursor.execute(
            "INSERT INTO tasks (task, deadline, status) VALUES (?, ?, ?)",
            (task, deadline, "pending"),
        )
        conn.commit()

        await update.message.reply_text(f"✅ Added task: {task}")

# ==============================
# DAILY CHECK-IN
# ==============================

CHAT_ID = 1265910148  # Keep your chat ID

async def daily_checkin(context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM tasks WHERE status='pending'")
    tasks = cursor.fetchall()

    if not tasks:
        message = "🎉 No pending tasks today. Great job!"
    else:
        message = "👋 Daily Check-in\n\nYou still have:\n\n"
        for task in tasks:
            message += f"{task[0]}. {task[1]}\n"
        message += "\nDid you complete any?"

    await context.bot.send_message(chat_id=CHAT_ID, text=message)

# ==============================
# TELEGRAM APPLICATION
# ==============================

application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("addtask", add_task))
application.add_handler(CommandHandler("tasks", show_tasks))
application.add_handler(CommandHandler("done", mark_done))
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, natural_language_handler)
)

application.job_queue.run_daily(
    daily_checkin,
    time=time(hour=20, minute=0),
)

# ==============================
# FLASK WEBHOOK SERVER
# ==============================

flask_app = Flask(__name__)

PORT = int(os.environ.get("PORT", 10000))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

# Create a global event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def init_app():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(
        url=f"{RENDER_EXTERNAL_URL}/{TOKEN}"
    )

loop.run_until_complete(init_app())


@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    loop.create_task(application.process_update(update))
    return "ok", 200


@flask_app.route("/")
def health():
    return "Bot is running", 200


if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=PORT)