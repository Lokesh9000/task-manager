from services.users import get_user
from utils.errors import NotFoundError, ValidationError

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
_PRIORITY_FILTER_VALUES = {str(p): p for p in range(MIN_PRIORITY, MAX_PRIORITY + 1)}

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1, "priority": 3},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1, "priority": 3},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2, "priority": 3},
}

def _validate_priority(priority: object) -> int:
    """Validate a task priority.

    Args:
        priority: The candidate priority value, where 1 is most urgent and
            5 is lowest.

    Returns:
        The validated priority.

    Raises:
        ValidationError: If priority is not an integer from 1 to 5. Booleans,
            strings, floats, and None are rejected.
    """
    if type(priority) is not int or not MIN_PRIORITY <= priority <= MAX_PRIORITY:
        raise ValidationError("priority", "must be an integer from 1 to 5")
    return priority

def process_order(task_id: int) -> dict:
    task = TASKS[task_id]
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

def create_task(title: str, user_id: int, priority: int = DEFAULT_PRIORITY) -> dict:
    """Create a new task.

    Args:
        title: The title of the task.
        user_id: The unique identifier for the user who owns the task.
        priority: The task priority from 1 (most urgent) to 5 (lowest).
            Defaults to 3.

    Returns:
        The newly created task record as a dictionary.

    Raises:
        ValidationError: If priority is not an integer from 1 to 5.
    """
    priority = _validate_priority(priority)
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title,
                     "done": False, "user_id": user_id, "priority": priority}
    return TASKS[new_id]

def update_task_priority(task_id: int, updates: object) -> dict:
    """Update the priority of an existing task.

    Args:
        task_id: The unique identifier for the task.
        updates: The requested changes. Must be a dictionary containing
            only the key "priority".

    Returns:
        The updated task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
        ValidationError: If updates is not a dictionary, contains a field
            other than priority, omits priority, or priority is not an
            integer from 1 to 5.
    """
    task = get_task(task_id)
    if type(updates) is not dict:
        raise ValidationError("request", "must be a JSON object")
    if any(field != "priority" for field in updates):
        raise ValidationError("request", "only priority can be updated")
    if "priority" not in updates:
        raise ValidationError("priority", "is required")
    task["priority"] = _validate_priority(updates["priority"])
    return task

def parse_priority_filter(values: list[str]) -> int | None:
    """Parse the raw priority filter values from a task listing request.

    Args:
        values: Every raw string supplied for the priority filter. An empty
            list means no filter was requested.

    Returns:
        The requested priority, or None if no filter was requested.

    Raises:
        ValidationError: If more than one value is supplied, or the value is
            not exactly one of the strings "1" to "5". Empty strings, padded
            values, signs, leading zeros, and decimals are rejected.
    """
    if not values:
        return None
    if len(values) != 1 or values[0] not in _PRIORITY_FILTER_VALUES:
        raise ValidationError("priority", "must be an integer from 1 to 5")
    return _PRIORITY_FILTER_VALUES[values[0]]

def list_tasks(priority: int | None = None) -> list[dict]:
    """Retrieve all tasks, optionally filtered by priority.

    Args:
        priority: If given, only tasks with this priority are returned.
            Defaults to None, which returns every task.

    Returns:
        A new list of task records. The list is empty if no task matches.

    Raises:
        ValidationError: If priority is given and is not an integer from 1 to 5.
    """
    if priority is None:
        return list(TASKS.values())
    priority = _validate_priority(priority)
    return [task for task in TASKS.values() if task["priority"] == priority]
