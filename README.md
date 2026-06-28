Proactive Personal Agent 🤖
A Telegram-based autonomous task agent that:

✅ Stores tasks with deadlines
✅ Sends proactive daily check-ins
✅ Supports natural language task detection
✅ Runs 24/7 (cloud deploy ready)
🚀 Features
Add tasks manually or via natural language
Deadline-aware reminders
SQLite persistence
Proactive scheduled notifications
Secure token handling with .env
🛠 Tech Stack
Python
python-telegram-bot
SQLite
APScheduler / JobQueue
Render (Deployment)
🔐 Setup
Clone the repo
Create a .env file:
text

TOKEN=your_telegram_bot_token
Install dependencies:
text

pip install -r requirements.txt
Run:
text

python bot.py
📌 Status
Currently building iteratively.
Next goal: Intelligent task prioritization and planning loop.