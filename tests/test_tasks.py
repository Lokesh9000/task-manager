import copy
import pytest
from app import app
from services.tasks import TASKS, create_task, process_order, get_task, get_tasks_for_user, update_task_priority, list_tasks, parse_priority_filter
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

def test_list_tasks_unfiltered(restore_tasks):
    result = list_tasks()
    assert result == list(TASKS.values())
    assert list_tasks(None) == list(TASKS.values())
    assert [task["id"] for task in result] == [1, 2, 3]

def test_list_tasks_matching_seeded(restore_tasks):
    result = list_tasks(3)
    assert [task["id"] for task in result] == [1, 2, 3]

@pytest.mark.parametrize("priority", [1, 2, 4, 5])
def test_list_tasks_no_match(restore_tasks, priority):
    assert list_tasks(priority) == []

def test_list_tasks_created_and_updated(restore_tasks):
    created = create_task("Water plants", 2, 1)
    update_task_priority(2, {"priority": 5})
    assert list_tasks(1) == [created]
    assert [task["id"] for task in list_tasks(5)] == [2]
    assert [task["id"] for task in list_tasks(3)] == [1, 3]

@pytest.mark.parametrize("priority", [True, False, "3", 3.0, 2.5, 0, 6, -1])
def test_list_tasks_invalid_priority(restore_tasks, priority):
    tasks_before = copy.deepcopy(TASKS)
    with pytest.raises(ValidationError) as exc_info:
        list_tasks(priority)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid priority: must be an integer from 1 to 5"
    assert TASKS == tasks_before

def test_list_tasks_does_not_mutate(restore_tasks):
    tasks_before = copy.deepcopy(TASKS)
    unfiltered = list_tasks()
    matching = list_tasks(3)
    assert list_tasks(1) == []
    assert TASKS == tasks_before
    unfiltered.clear()
    matching.clear()
    assert TASKS == tasks_before

@pytest.mark.parametrize("values, expected", [
    ([], None),
    (["1"], 1),
    (["2"], 2),
    (["3"], 3),
    (["4"], 4),
    (["5"], 5),
])
def test_parse_priority_filter_valid(restore_tasks, values, expected):
    assert parse_priority_filter(values) == expected

@pytest.mark.parametrize("values", [
    [""], ["0"], ["6"], ["-1"], ["3.0"], ["2.5"], ["true"], ["abc"],
    [" 3"], ["3 "], ["03"], ["+3"], ["٣"], ["9" * 5000],
    ["1", "2"], ["3", "3"],
])
def test_parse_priority_filter_invalid(restore_tasks, values):
    with pytest.raises(ValidationError) as exc_info:
        parse_priority_filter(values)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid priority: must be an integer from 1 to 5"

def test_api_list_tasks_unfiltered(restore_tasks, client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert response.get_json() == list(TASKS.values())
    assert all(set(task) == {"id", "title", "done", "user_id", "priority"}
               for task in response.get_json())

def test_api_list_tasks_matching_seeded(restore_tasks, client):
    response = client.get("/api/tasks?priority=3")
    assert response.status_code == 200
    assert [task["id"] for task in response.get_json()] == [1, 2, 3]

@pytest.mark.parametrize("priority", [1, 2, 4, 5])
def test_api_list_tasks_no_match(restore_tasks, client, priority):
    response = client.get(f"/api/tasks?priority={priority}")
    assert response.status_code == 200
    assert response.get_json() == []

def test_api_list_tasks_created_and_updated(restore_tasks, client):
    created = client.post("/api/tasks", json={"title": "Water plants", "user_id": 2,
                                              "priority": 1}).get_json()
    client.patch("/api/tasks/2", json={"priority": 5})
    assert client.get("/api/tasks?priority=1").get_json() == [created]
    assert [task["id"] for task in client.get("/api/tasks?priority=5").get_json()] == [2]
    assert [task["id"] for task in client.get("/api/tasks?priority=3").get_json()] == [1, 3]

@pytest.mark.parametrize("query", [
    "priority=", "priority", "priority=0", "priority=6", "priority=-1",
    "priority=3.0", "priority=2.5", "priority=true", "priority=abc",
    "priority=%203", "priority=3%20", "priority=+3", "priority=03",
    "priority=1&priority=2",
])
def test_api_list_tasks_invalid_priority(restore_tasks, client, query):
    tasks_before = copy.deepcopy(TASKS)
    response = client.get(f"/api/tasks?{query}")
    assert response.status_code == 422
    assert response.get_json() == {
        "error": "Invalid priority: must be an integer from 1 to 5"}
    assert TASKS == tasks_before

def test_api_list_tasks_does_not_mutate(restore_tasks, client):
    tasks_before = copy.deepcopy(TASKS)
    assert client.get("/api/tasks").status_code == 200
    assert client.get("/api/tasks?priority=3").status_code == 200
    assert client.get("/api/tasks?priority=1").get_json() == []
    assert TASKS == tasks_before
