import copy

import pytest

from app import app
from services.users import (
    USERS,
    create_user,
    get_notification_pref,
    get_user,
    list_users,
    update_notification_pref,
)
from utils.errors import NotFoundError, ValidationError

INVALID_PREF_MESSAGE = "Invalid notification_pref: must be one of: email, sms, none"
INVALID_PREFS = [None, "", "push", "EMAIL", " email", "email ", 1, True, ["email"], {"a": 1}]

@pytest.fixture
def restore_users():
    snapshot = copy.deepcopy(USERS)
    try:
        yield
    finally:
        USERS.clear()
        USERS.update(snapshot)

@pytest.fixture
def client():
    return app.test_client()

def test_seed_users_have_default_notification_pref(restore_users):
    assert [USERS[user_id]["notification_pref"] for user_id in (1, 2)] == ["none", "none"]

def test_create_user_default_notification_pref(restore_users):
    expected_id = max(USERS.keys()) + 1
    result = create_user("Cara", "cara@example.com")
    assert result == {"id": expected_id, "name": "Cara", "email": "cara@example.com",
                      "notification_pref": "none"}
    assert USERS[expected_id] == result

def test_list_users_returns_every_user_with_notification_pref(restore_users):
    update_notification_pref(2, {"notification_pref": "sms"})
    result = list_users()
    assert result == list(USERS.values())
    assert [user["id"] for user in result] == [1, 2]
    assert [user["notification_pref"] for user in result] == ["none", "sms"]

def test_list_users_returns_new_list(restore_users):
    users_before = copy.deepcopy(USERS)
    result = list_users()
    assert result is not list_users()
    result.clear()
    assert USERS == users_before
    assert len(list_users()) == len(users_before)

def test_get_user_includes_notification_pref(restore_users):
    assert get_user(1) == {"id": 1, "name": "Alice", "email": "alice@example.com",
                           "notification_pref": "none"}

def test_get_notification_pref_valid(restore_users):
    assert get_notification_pref(1) == "none"
    USERS[2]["notification_pref"] = "email"
    assert get_notification_pref(2) == "email"

def test_get_notification_pref_unknown_user(restore_users):
    with pytest.raises(NotFoundError) as exc_info:
        get_notification_pref(999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "User not found"

@pytest.mark.parametrize("pref", ["email", "sms", "none"])
def test_update_notification_pref_valid(restore_users, pref):
    USERS[1]["notification_pref"] = "email" if pref == "none" else "none"
    users_before = copy.deepcopy(USERS)
    result = update_notification_pref(1, {"notification_pref": pref})
    assert result == {**users_before[1], "notification_pref": pref}
    assert USERS[1] == result
    assert get_notification_pref(1) == pref
    assert USERS[2] == users_before[2]
    assert set(USERS.keys()) == set(users_before.keys())

@pytest.mark.parametrize("pref", INVALID_PREFS)
def test_update_notification_pref_invalid_value(restore_users, pref):
    users_before = copy.deepcopy(USERS)
    with pytest.raises(ValidationError) as exc_info:
        update_notification_pref(1, {"notification_pref": pref})
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == INVALID_PREF_MESSAGE
    assert USERS == users_before

@pytest.mark.parametrize("updates, message", [
    ({}, "Invalid notification_pref: is required"),
    ({"name": "x"}, "Invalid request: only notification_pref can be updated"),
    ({"notification_pref": "sms", "name": "x"},
     "Invalid request: only notification_pref can be updated"),
    ([], "Invalid request: must be a JSON object"),
    (None, "Invalid request: must be a JSON object"),
])
def test_update_notification_pref_invalid_updates(restore_users, updates, message):
    users_before = copy.deepcopy(USERS)
    with pytest.raises(ValidationError) as exc_info:
        update_notification_pref(1, updates)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == message
    assert USERS == users_before

@pytest.mark.parametrize("updates", [
    {"notification_pref": "sms"},
    {"notification_pref": "push"},
    {"name": "x"},
    {},
    [],
    None,
])
def test_update_notification_pref_unknown_user(restore_users, updates):
    users_before = copy.deepcopy(USERS)
    with pytest.raises(NotFoundError) as exc_info:
        update_notification_pref(999, updates)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "User not found"
    assert USERS == users_before

def test_api_list_users(restore_users, client):
    USERS[2]["notification_pref"] = "sms"
    response = client.get("/api/users")
    assert response.status_code == 200
    body = response.get_json()
    assert body == list(USERS.values())
    assert [user["notification_pref"] for user in body] == ["none", "sms"]

def test_api_get_user_includes_notification_pref(restore_users, client):
    response = client.get("/api/users/1")
    assert response.status_code == 200
    assert response.get_json() == {"id": 1, "name": "Alice", "email": "alice@example.com",
                                   "notification_pref": "none"}

def test_api_get_notification_pref(restore_users, client):
    response = client.get("/api/users/1/notifications")
    assert response.status_code == 200
    assert response.get_json() == {"notification_pref": "none"}

def test_api_get_notification_pref_unknown_user(restore_users, client):
    response = client.get("/api/users/999/notifications")
    assert response.status_code == 404
    assert response.get_json() == {"error": "User not found"}

@pytest.mark.parametrize("pref", ["email", "sms", "none"])
def test_api_update_notification_pref_valid(restore_users, client, pref):
    USERS[1]["notification_pref"] = "email" if pref == "none" else "none"
    users_before = copy.deepcopy(USERS)
    response = client.patch("/api/users/1/notifications", json={"notification_pref": pref})
    assert response.status_code == 200
    assert response.get_json() == {"notification_pref": pref}
    assert USERS[1] == {**users_before[1], "notification_pref": pref}
    assert USERS[2] == users_before[2]
    assert client.get("/api/users/1/notifications").get_json() == {"notification_pref": pref}
    assert client.get("/api/users/1").get_json() == {**users_before[1],
                                                     "notification_pref": pref}
    assert client.get("/api/users").get_json() == [
        {**users_before[1], "notification_pref": pref}, users_before[2]]

@pytest.mark.parametrize("pref", INVALID_PREFS)
def test_api_update_notification_pref_invalid_value(restore_users, client, pref):
    users_before = copy.deepcopy(USERS)
    response = client.patch("/api/users/1/notifications", json={"notification_pref": pref})
    assert response.status_code == 422
    assert response.get_json() == {"error": INVALID_PREF_MESSAGE}
    assert USERS == users_before

@pytest.mark.parametrize("body, message", [
    ({}, "Invalid notification_pref: is required"),
    ({"name": "x"}, "Invalid request: only notification_pref can be updated"),
    ({"notification_pref": "sms", "name": "x"},
     "Invalid request: only notification_pref can be updated"),
    ([], "Invalid request: must be a JSON object"),
    (["email"], "Invalid request: must be a JSON object"),
])
def test_api_update_notification_pref_invalid_body(restore_users, client, body, message):
    users_before = copy.deepcopy(USERS)
    response = client.patch("/api/users/1/notifications", json=body)
    assert response.status_code == 422
    assert response.get_json() == {"error": message}
    assert USERS == users_before

def test_api_update_notification_pref_null_body(restore_users, client):
    users_before = copy.deepcopy(USERS)
    response = client.patch("/api/users/1/notifications", data="null",
                            content_type="application/json")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid request: must be a JSON object"}
    assert USERS == users_before

@pytest.mark.parametrize("body", [{"notification_pref": "sms"}, {"notification_pref": "push"}])
def test_api_update_notification_pref_unknown_user(restore_users, client, body):
    users_before = copy.deepcopy(USERS)
    response = client.patch("/api/users/999/notifications", json=body)
    assert response.status_code == 404
    assert response.get_json() == {"error": "User not found"}
    assert USERS == users_before
