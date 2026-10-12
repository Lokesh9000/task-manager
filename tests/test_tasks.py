import copy
import pytest
from services.tasks import process_order, get_task, get_tasks_for_user, TASKS, create_task, update_task_priority
from utils.errors import NotFoundError, ValidationError

@pytest.fixture
def restore_tasks():
    snapshot = copy.deepcopy(TASKS)
    try:
        yield
    finally:
        TASKS.clear()
        TASKS.update(snapshot)

def test_process_order_valid():
    result = process_order(1)
    assert result["done"] is True

def test_process_order_invalid():
    with pytest.raises(Exception):
        process_order(999)

def test_get_task_valid():
    result = get_task(2)
    assert result["title"] == "Write report"

def test_get_task_invalid():
    with pytest.raises(NotFoundError) as exc_info:
        get_task(999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Task not found"

def test_get_tasks_for_user_valid():
    result = get_tasks_for_user(1)
    assert [task["id"] for task in result] == [1, 2]
    assert all(task["user_id"] == 1 for task in result)

def test_get_tasks_for_user_invalid():
    with pytest.raises(NotFoundError) as exc_info:
        get_tasks_for_user(999)
    assert exc_info.value.message == "User not found"

def test_seed_tasks_have_priority():
    for task in TASKS.values():
        assert type(task["priority"]) is int
        assert 1 <= task["priority"] <= 5

def test_create_task_default_priority(restore_tasks):
    result = create_task("Default priority task", 1)
    assert result["priority"] == 3
    assert TASKS[result["id"]] is result

def test_create_task_with_priority(restore_tasks):
    urgent = create_task("Urgent task", 1, 1)
    low = create_task("Low task", 1, priority=5)
    assert TASKS[urgent["id"]]["priority"] == 1
    assert TASKS[low["id"]]["priority"] == 5

@pytest.mark.parametrize("priority", [0, 6, -1, "3", 2.5, None, True])
def test_create_task_invalid_priority(restore_tasks, priority):
    task_count = len(TASKS)
    with pytest.raises(ValidationError) as exc_info:
        create_task("Invalid priority task", 1, priority)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid priority: must be an integer from 1 to 5"
    assert len(TASKS) == task_count

@pytest.mark.parametrize("priority", [1, 2, 3, 4, 5])
def test_update_task_priority_valid(restore_tasks, priority):
    result = update_task_priority(1, priority)
    assert result["priority"] == priority
    assert TASKS[1]["priority"] == priority
    assert result is TASKS[1]

def test_update_task_priority_preserves_other_data(restore_tasks):
    snapshot = copy.deepcopy(TASKS)
    update_task_priority(1, 5)
    assert TASKS[1] == {**snapshot[1], "priority": 5}
    assert TASKS[2] == snapshot[2]
    assert TASKS[3] == snapshot[3]
    assert len(TASKS) == len(snapshot)

@pytest.mark.parametrize("priority", [0, 6, -1, "3", 2.5, 3.0, None, True, False])
def test_update_task_priority_invalid(restore_tasks, priority):
    snapshot = copy.deepcopy(TASKS)
    with pytest.raises(ValidationError) as exc_info:
        update_task_priority(1, priority)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid priority: must be an integer from 1 to 5"
    assert TASKS == snapshot

def test_update_task_priority_missing_task(restore_tasks):
    snapshot = copy.deepcopy(TASKS)
    with pytest.raises(NotFoundError) as exc_info:
        update_task_priority(999, 2)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Task not found"
    assert 999 not in TASKS
    assert TASKS == snapshot
