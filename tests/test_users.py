import copy

import pytest

from services.users import (
    USERS,
    create_user,
    get_notification_pref,
    list_users,
    set_notification_pref,
)
from utils.errors import NotFoundError, ValidationError

INVALID_PREF_MESSAGE = "Invalid notification_pref: must be one of email, sms, none, or null"


@pytest.fixture
def restore_users():
    snapshot = copy.deepcopy(USERS)
    try:
        yield
    finally:
        USERS.clear()
        USERS.update(snapshot)

def test_seed_users_have_default_notification_pref(restore_users):
    assert sorted(USERS) == [1, 2]
    for user in USERS.values():
        assert "notification_pref" in user
        assert user["notification_pref"] is None

def test_create_user_default_notification_pref(restore_users):
    result = create_user("Carol", "carol@example.com")
    assert "notification_pref" in result
    assert result["notification_pref"] is None
    assert USERS[result["id"]]["notification_pref"] is None

def test_list_users(restore_users):
    snapshot = copy.deepcopy(USERS)
    result = list_users()
    assert result == list(USERS.values())
    assert [user["id"] for user in result] == [1, 2]
    result.clear()
    assert USERS == snapshot
    assert list_users() == list(USERS.values())

def test_get_notification_pref_default(restore_users):
    assert get_notification_pref(1) is None
    assert get_notification_pref(2) is None

def test_get_notification_pref_after_set(restore_users):
    set_notification_pref(1, "sms")
    assert get_notification_pref(1) == "sms"
    assert get_notification_pref(2) is None

@pytest.mark.parametrize("value", ["email", "sms", "none"])
def test_set_notification_pref_valid(restore_users, value):
    snapshot = copy.deepcopy(USERS)
    result = set_notification_pref(1, value)
    assert result == {**snapshot[1], "notification_pref": value}
    assert result is USERS[1]
    assert USERS[1] == {**snapshot[1], "notification_pref": value}
    assert USERS[2] == snapshot[2]
    assert len(USERS) == len(snapshot)

@pytest.mark.parametrize("value", ["email", "sms", "none"])
def test_set_notification_pref_none_resets(restore_users, value):
    snapshot = copy.deepcopy(USERS)
    set_notification_pref(1, value)
    result = set_notification_pref(1, None)
    assert result["notification_pref"] is None
    assert USERS[1]["notification_pref"] is None
    assert get_notification_pref(1) is None
    assert USERS == snapshot

@pytest.mark.parametrize(
    "value",
    ["Email", "EMAIL", "", " email", "push", 1, 0, True, False, 2.5, [], ["email"], {}],
)
def test_set_notification_pref_invalid(restore_users, value):
    snapshot = copy.deepcopy(USERS)
    with pytest.raises(ValidationError) as exc_info:
        set_notification_pref(1, value)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == INVALID_PREF_MESSAGE
    assert USERS == snapshot

def test_get_notification_pref_missing_user(restore_users):
    snapshot = copy.deepcopy(USERS)
    with pytest.raises(NotFoundError) as exc_info:
        get_notification_pref(999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "User not found"
    assert USERS == snapshot

@pytest.mark.parametrize("value", ["email", "push"])
def test_set_notification_pref_missing_user(restore_users, value):
    snapshot = copy.deepcopy(USERS)
    with pytest.raises(NotFoundError) as exc_info:
        set_notification_pref(999, value)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "User not found"
    assert 999 not in USERS
    assert USERS == snapshot
