from agent.task_manager import add_task, get_pending_tasks, mark_task_done

def create_task_from_text(task, deadline=None):
    add_task(task, deadline)

def list_tasks():
    return get_pending_tasks()

def complete_task(task_id):
    mark_task_done(task_id)