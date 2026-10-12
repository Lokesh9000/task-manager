import copy
import pytest
from app import app
from services.tasks import TASKS, create_task, process_order, get_task, get_tasks_for_user, update_task_priority
from utils.errors import NotFoundError, ValidationError

@pytest.fixture
def restore_tasks():
    snapshot = copy.deepcopy(TASKS)
    try:
        yield
    finally:
        TASKS.clear()
        TASKS.update(snapshot)

@pytest.fixture
def client():
    return app.test_client()

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

def test_seed_tasks_have_default_priority(restore_tasks):
    assert [TASKS[task_id]["priority"] for task_id in (1, 2, 3)] == [3, 3, 3]

def test_create_task_default_priority(restore_tasks):
    expected_id = max(TASKS.keys()) + 1
    result = create_task("Water plants", 2)
    assert result == {"id": expected_id, "title": "Water plants",
                      "done": False, "user_id": 2, "priority": 3}
    assert TASKS[expected_id] is result

@pytest.mark.parametrize("priority", [1, 5])
def test_create_task_explicit_priority(restore_tasks, priority):
    result = create_task("Water plants", 2, priority)
    assert result["priority"] == priority

@pytest.mark.parametrize("priority", [True, False, "3", 3.0, 2.5, 0, 6, -1, None])
def test_create_task_invalid_priority(restore_tasks, priority):
    keys_before = set(TASKS.keys())
    with pytest.raises(ValidationError) as exc_info:
        create_task("Water plants", 2, priority)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid priority: must be an integer from 1 to 5"
    assert set(TASKS.keys()) == keys_before

def test_api_create_task_without_priority(restore_tasks, client):
    expected_id = max(TASKS.keys()) + 1
    response = client.post("/api/tasks", json={"title": "Water plants", "user_id": 2})
    assert response.status_code == 201
    assert response.get_json() == {"id": expected_id, "title": "Water plants",
                                   "done": False, "user_id": 2, "priority": 3}
    assert TASKS[expected_id]["priority"] == 3

@pytest.mark.parametrize("priority", [1, 5])
def test_api_create_task_with_priority(restore_tasks, client, priority):
    response = client.post("/api/tasks", json={"title": "Water plants", "user_id": 2,
                                               "priority": priority})
    assert response.status_code == 201
    assert response.get_json()["priority"] == priority

@pytest.mark.parametrize("priority", [None, True, False, "3", 3.0, 2.5, 0, 6, -1])
def test_api_create_task_invalid_priority(restore_tasks, client, priority):
    tasks_before = copy.deepcopy(TASKS)
    response = client.post("/api/tasks", json={"title": "Water plants", "user_id": 2,
                                               "priority": priority})
    assert response.status_code == 422
    assert response.get_json() == {
        "error": "Invalid priority: must be an integer from 1 to 5"}
    assert TASKS == tasks_before

@pytest.mark.parametrize("priority", [1, 5])
def test_update_task_priority_valid(restore_tasks, priority):
    tasks_before = copy.deepcopy(TASKS)
    result = update_task_priority(2, {"priority": priority})
    assert result is TASKS[2]
    assert result == {**tasks_before[2], "priority": priority}
    assert TASKS[1] == tasks_before[1]
    assert TASKS[3] == tasks_before[3]

@pytest.mark.parametrize("priority", [True, False, "3", 3.0, 2.5, 0, 6, -1, None])
def test_update_task_priority_invalid_priority(restore_tasks, priority):
    tasks_before = copy.deepcopy(TASKS)
    with pytest.raises(ValidationError) as exc_info:
        update_task_priority(2, {"priority": priority})
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid priority: must be an integer from 1 to 5"
    assert TASKS == tasks_before

@pytest.mark.parametrize("updates, message", [
    ({}, "Invalid priority: is required"),
    ({"title": "x"}, "Invalid request: only priority can be updated"),
    ({"priority": 2, "title": "x"}, "Invalid request: only priority can be updated"),
    ({"priority": 2, "done": True}, "Invalid request: only priority can be updated"),
    ([], "Invalid request: must be a JSON object"),
    (None, "Invalid request: must be a JSON object"),
])
def test_update_task_priority_invalid_updates(restore_tasks, updates, message):
    tasks_before = copy.deepcopy(TASKS)
    with pytest.raises(ValidationError) as exc_info:
        update_task_priority(2, updates)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == message
    assert TASKS == tasks_before

@pytest.mark.parametrize("updates", [{"priority": 2}, {"priority": 9}])
def test_update_task_priority_not_found(restore_tasks, updates):
    tasks_before = copy.deepcopy(TASKS)
    with pytest.raises(NotFoundError) as exc_info:
        update_task_priority(999, updates)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Task not found"
    assert TASKS == tasks_before

@pytest.mark.parametrize("priority", [1, 5])
def test_api_update_task_priority(restore_tasks, client, priority):
    expected = {**copy.deepcopy(TASKS[2]), "priority": priority}
    response = client.patch("/api/tasks/2", json={"priority": priority})
    assert response.status_code == 200
    assert response.get_json() == expected
    assert TASKS[2]["priority"] == priority
    assert client.get("/api/tasks/2").get_json() == expected

@pytest.mark.parametrize("priority", [None, True, False, "3", 3.0, 2.5, 0, 6, -1])
def test_api_update_task_invalid_priority(restore_tasks, client, priority):
    tasks_before = copy.deepcopy(TASKS)
    response = client.patch("/api/tasks/2", json={"priority": priority})
    assert response.status_code == 422
    assert response.get_json() == {
        "error": "Invalid priority: must be an integer from 1 to 5"}
    assert TASKS == tasks_before

@pytest.mark.parametrize("body, message", [
    ({}, "Invalid priority: is required"),
    ({"title": "x"}, "Invalid request: only priority can be updated"),
    ({"priority": 2, "title": "x"}, "Invalid request: only priority can be updated"),
    ([], "Invalid request: must be a JSON object"),
])
def test_api_update_task_invalid_body(restore_tasks, client, body, message):
    tasks_before = copy.deepcopy(TASKS)
    response = client.patch("/api/tasks/2", json=body)
    assert response.status_code == 422
    assert response.get_json() == {"error": message}
    assert TASKS == tasks_before

def test_api_update_task_null_body(restore_tasks, client):
    tasks_before = copy.deepcopy(TASKS)
    response = client.patch("/api/tasks/2", data="null",
                            content_type="application/json")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid request: must be a JSON object"}
    assert TASKS == tasks_before

def test_api_update_task_not_found(restore_tasks, client):
    tasks_before = copy.deepcopy(TASKS)
    response = client.patch("/api/tasks/999", json={"priority": 2})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}
    assert TASKS == tasks_before
