# ==============================
# IMPORTS
# ==============================

import os
from datetime import datetime, timedelta, time

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Import your architecture layers
from agent.engine import create_task_from_text, list_tasks, complete_task
from db.database import init_db


# ==============================
# ENVIRONMENT SETUP
# ==============================

load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN not found in environment variables.")

# Initialize database once when bot starts
init_db()


# ==============================
# TELEGRAM HANDLERS
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Proactive Personal Agent\n\n"
        "/addtask Task | YYYY-MM-DD\n"
        "/tasks\n"
        "/done <id>"
    )


async def add_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)

    if not text:
        await update.message.reply_text("Usage: /addtask Task | YYYY-MM-DD")
        return

    if "|" in text:
        task, deadline = map(str.strip, text.split("|"))
    else:
        task = text
        deadline = None

    create_task_from_text(task, deadline)
    await update.message.reply_text(f"✅ Task added: {task}")


async def show_tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = list_tasks()

    if not tasks:
        await update.message.reply_text("🎉 No pending tasks.")
        return

    message = "📋 Pending Tasks:\n\n"

    for task in tasks:
        deadline_info = f" (Due: {task[2]})" if task[2] else ""
        message += f"{task[0]}. {task[1]}{deadline_info}\n"

    await update.message.reply_text(message)


async def done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /done <id>")
        return

    task_id = context.args[0]
    complete_task(task_id)

    await update.message.reply_text(f"✅ Task {task_id} marked as done!")


async def natural_language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    deadline = None
    if "tomorrow" in text:
        deadline = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    trigger_phrases = ["i need to", "i have to", "i should", "remind me to"]

    for phrase in trigger_phrases:
        if phrase in text:
            task = text.replace(phrase, "").strip()
            create_task_from_text(task, deadline)
            await update.message.reply_text(f"✅ Added task: {task}")
            return


# ==============================
# DAILY CHECK-IN
# ==============================

CHAT_ID = 1265910148  # keep your chat ID


async def daily_checkin(context: ContextTypes.DEFAULT_TYPE):
    tasks = list_tasks()

    if not tasks:
        message = "🎉 No pending tasks today."
    else:
        message = "👋 Daily Check-in\n\nYou still have:\n\n"
        for task in tasks:
            message += f"{task[0]}. {task[1]}\n"
        message += "\nDid you complete any?"

    await context.bot.send_message(chat_id=CHAT_ID, text=message)


# ==============================
# APPLICATION SETUP
# ==============================

application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("addtask", add_task_handler))
application.add_handler(CommandHandler("tasks", show_tasks_handler))
application.add_handler(CommandHandler("done", done_handler))
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, natural_language_handler)
)

application.job_queue.run_daily(
    daily_checkin,
    time=time(hour=20, minute=0),
)

print("Bot running...")
application.run_polling()