from services.users import get_user
from utils.errors import NotFoundError, ValidationError

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
PRIORITY_REASON = "must be an integer from 1 to 5"

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1, "priority": 3},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1, "priority": 3},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2, "priority": 3},
}

def _validate_priority(priority: int) -> None:
    """Validate a task priority.

    Args:
        priority: The priority value to validate.

    Raises:
        ValidationError: If priority is not an integer from 1 to 5.
    """
    if (isinstance(priority, bool) or not isinstance(priority, int)
            or not MIN_PRIORITY <= priority <= MAX_PRIORITY):
        raise ValidationError("priority", PRIORITY_REASON)

def process_order(task_id: int) -> dict:
    """Mark a task as done.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The updated task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    task = get_task(task_id)
    task["done"] = True
    return task

def get_task(task_id: int) -> dict:
    """Retrieve a task by ID.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    return TASKS[task_id]

def get_tasks_for_user(user_id: int) -> list[dict]:
    """Retrieve all tasks belonging to a user.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        A list of task records owned by the user. The list is empty if the
        user has no tasks.

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    get_user(user_id)
    return [task for task in TASKS.values() if task["user_id"] == user_id]

def list_tasks(priority: int | None = None) -> list[dict]:
    """Retrieve all tasks, optionally filtered by priority.

    Args:
        priority: The priority from 1 (urgent) to 5 (low) to filter by. If
            None, all tasks are returned.

    Returns:
        A new list of matching task records. The list is empty if no task
        has the given priority.

    Raises:
        ValidationError: If priority is given and is not an integer from 1 to 5.
    """
    if priority is None:
        return list(TASKS.values())
    _validate_priority(priority)
    return [task for task in TASKS.values() if task["priority"] == priority]

def create_task(title: str, user_id: int, priority: int = DEFAULT_PRIORITY) -> dict:
    """Create a new task.

    Args:
        title: The title of the task.
        user_id: The unique identifier for the user who owns the task.
        priority: The task priority from 1 (urgent) to 5 (low). Defaults to 3.

    Returns:
        The newly created task record as a dictionary.

    Raises:
        ValidationError: If priority is not an integer from 1 to 5.
    """
    _validate_priority(priority)
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title,
                     "done": False, "user_id": user_id, "priority": priority}
    return TASKS[new_id]

def update_task_priority(task_id: int, priority: int) -> dict:
    """Update the priority of an existing task.

    Args:
        task_id: The unique identifier for the task.
        priority: The new priority from 1 (urgent) to 5 (low).

    Returns:
        The updated task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
        ValidationError: If priority is not an integer from 1 to 5.
    """
    task = get_task(task_id)
    _validate_priority(priority)
    task["priority"] = priority
    return task
