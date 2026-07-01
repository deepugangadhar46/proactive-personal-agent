from db.database import get_connection

def add_task(task, deadline=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks (task, deadline, status) VALUES (?, ?, ?)",
        (task, deadline, "pending")
    )

    conn.commit()
    conn.close()

def get_pending_tasks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE status='pending'")
    tasks = cursor.fetchall()

    conn.close()
    return tasks

def mark_task_done(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE tasks SET status='done' WHERE id=?", (task_id,))
    conn.commit()
    conn.close()