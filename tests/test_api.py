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
