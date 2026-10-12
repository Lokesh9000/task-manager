import copy

import pytest

from app import app
from services.tasks import TASKS


@pytest.fixture
def client():
    return app.test_client()

@pytest.fixture(autouse=True)
def restore_tasks():
    snapshot = copy.deepcopy(TASKS)
    try:
        yield
    finally:
        TASKS.clear()
        TASKS.update(snapshot)

def test_create_task_without_priority(client):
    response = client.post("/api/tasks", json={"title": "No priority task", "user_id": 1})
    assert response.status_code == 201
    body = response.get_json()
    assert body["priority"] == 3
    assert body["title"] == "No priority task"
    assert body["user_id"] == 1
    assert body["done"] is False
    assert TASKS[body["id"]]["priority"] == 3

@pytest.mark.parametrize("priority", [1, 2, 3, 4, 5])
def test_create_task_with_priority(client, priority):
    response = client.post(
        "/api/tasks",
        json={"title": "Priority task", "user_id": 1, "priority": priority},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["priority"] == priority
    assert TASKS[body["id"]]["priority"] == priority

@pytest.mark.parametrize("priority", [None, True, False, "3", 2.5, 3.0, 0, 6, -1])
def test_create_task_invalid_priority(client, priority):
    task_count = len(TASKS)
    response = client.post(
        "/api/tasks",
        json={"title": "Invalid priority task", "user_id": 1, "priority": priority},
    )
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid priority: must be an integer from 1 to 5"}
    assert len(TASKS) == task_count

@pytest.mark.parametrize("priority", [1, 2, 3, 4, 5])
def test_update_task_priority(client, priority):
    original = copy.deepcopy(TASKS[1])
    response = client.patch("/api/tasks/1", json={"priority": priority})
    assert response.status_code == 200
    assert response.get_json() == {**original, "priority": priority}
    assert TASKS[1]["priority"] == priority
    assert client.get("/api/tasks/1").get_json()["priority"] == priority

def test_update_task_priority_leaves_other_tasks_unchanged(client):
    snapshot = copy.deepcopy(TASKS)
    response = client.patch("/api/tasks/1", json={"priority": 5})
    assert response.status_code == 200
    assert TASKS[2] == snapshot[2]
    assert TASKS[3] == snapshot[3]
    assert len(TASKS) == len(snapshot)

def test_update_task_ignores_other_fields(client):
    original = copy.deepcopy(TASKS[1])
    response = client.patch(
        "/api/tasks/1",
        json={"priority": 2, "title": "Changed", "done": True},
    )
    assert response.status_code == 200
    assert response.get_json() == {**original, "priority": 2}
    assert TASKS[1] == {**original, "priority": 2}

@pytest.mark.parametrize("priority", [None, True, False, "3", 2.5, 3.0, 0, 6, -1])
def test_update_task_invalid_priority(client, priority):
    snapshot = copy.deepcopy(TASKS)
    response = client.patch("/api/tasks/1", json={"priority": priority})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid priority: must be an integer from 1 to 5"}
    assert TASKS == snapshot

@pytest.mark.parametrize("body", [{}, {"title": "No priority"}])
def test_update_task_missing_priority(client, body):
    snapshot = copy.deepcopy(TASKS)
    response = client.patch("/api/tasks/1", json=body)
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid priority: is required"}
    assert TASKS == snapshot

@pytest.mark.parametrize("body", ["[]", "[1]", '"3"', "3", "null"])
def test_update_task_non_object_body(client, body):
    snapshot = copy.deepcopy(TASKS)
    response = client.patch("/api/tasks/1", data=body, content_type="application/json")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid request body: must be a JSON object"}
    assert TASKS == snapshot

def test_update_task_non_object_body_checked_before_lookup(client):
    snapshot = copy.deepcopy(TASKS)
    response = client.patch("/api/tasks/999", json=[])
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid request body: must be a JSON object"}
    assert TASKS == snapshot

def test_update_task_not_found(client):
    snapshot = copy.deepcopy(TASKS)
    response = client.patch("/api/tasks/999", json={"priority": 2})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}
    assert TASKS == snapshot

def test_update_task_not_found_with_invalid_priority(client):
    snapshot = copy.deepcopy(TASKS)
    response = client.patch("/api/tasks/999", json={"priority": 9})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}
    assert TASKS == snapshot

def test_list_tasks_without_priority(client):
    snapshot = copy.deepcopy(TASKS)
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert response.get_json() == list(TASKS.values())
    assert [task["id"] for task in response.get_json()] == [1, 2, 3]
    assert TASKS == snapshot

@pytest.mark.parametrize(
    "priority, expected_ids",
    [(1, [1]), (2, []), (3, [3]), (4, []), (5, [2])],
)
def test_list_tasks_with_priority(client, priority, expected_ids):
    TASKS[1]["priority"] = 1
    TASKS[2]["priority"] = 5
    snapshot = copy.deepcopy(TASKS)
    response = client.get(f"/api/tasks?priority={priority}")
    assert response.status_code == 200
    assert response.get_json() == [TASKS[task_id] for task_id in expected_ids]
    assert TASKS == snapshot

def test_list_tasks_no_matches(client):
    snapshot = copy.deepcopy(TASKS)
    response = client.get("/api/tasks?priority=1")
    assert response.status_code == 200
    assert response.get_json() == []
    assert TASKS == snapshot

def test_list_tasks_after_patch(client):
    client.patch("/api/tasks/1", json={"priority": 5})
    response = client.get("/api/tasks?priority=5")
    assert response.status_code == 200
    assert response.get_json() == [TASKS[1]]
    remaining = client.get("/api/tasks?priority=3").get_json()
    assert [task["id"] for task in remaining] == [2, 3]

@pytest.mark.parametrize(
    "value",
    ["abc", "", "3.0", "2.5", "0", "6", "-1", "+3", " 3", "3 ", "true", "null",
     "1,2", "٣", "9" * 5000],
)
def test_list_tasks_invalid_priority(client, value):
    snapshot = copy.deepcopy(TASKS)
    response = client.get("/api/tasks", query_string={"priority": value})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid priority: must be an integer from 1 to 5"}
    assert TASKS == snapshot

@pytest.mark.parametrize(
    "query",
    ["priority=1&priority=2", "priority=3&priority=3", "priority=3&priority=abc",
     "priority=abc&priority=3", "priority=&priority=3"],
)
def test_list_tasks_repeated_priority(client, query):
    snapshot = copy.deepcopy(TASKS)
    response = client.get(f"/api/tasks?{query}")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid priority: must be provided at most once"}
    assert TASKS == snapshot

@pytest.mark.parametrize("query", ["done=true", "Priority=3", "user_id=1"])
def test_list_tasks_ignores_other_params(client, query):
    TASKS[1]["priority"] = 1
    response = client.get(f"/api/tasks?{query}")
    assert response.status_code == 200
    assert response.get_json() == list(TASKS.values())
