from utils.errors import NotFoundError, ValidationError

NOTIFICATION_PREFS: tuple[str, ...] = ("email", "sms", "none")
DEFAULT_NOTIFICATION_PREF = None

USERS: dict[int, dict] = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com", "notification_pref": None},
    2: {"id": 2, "name": "Bob",   "email": "bob@example.com", "notification_pref": None},
}

def get_user(user_id: int) -> dict:
    """Retrieve a user by ID.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The user record as a dictionary.

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    if user_id not in USERS:
        raise NotFoundError("User")
    return USERS[user_id]

def create_user(name: str, email: str) -> dict:
    """Create a new user.

    Args:
        name: The user's display name.
        email: The user's email address.

    Returns:
        The newly created user record.

    Raises:
        ValidationError: If name or email is empty.
    """
    if not name or not name.strip():
        raise ValidationError("name", "cannot be empty")
    if not email or "@" not in email:
        raise ValidationError("email", "must be a valid email address")
    new_id = max(USERS.keys()) + 1
    USERS[new_id] = {
        "id": new_id,
        "name": name,
        "email": email,
        "notification_pref": DEFAULT_NOTIFICATION_PREF,
    }
    return USERS[new_id]

def list_users() -> list[dict]:
    """List all users.

    Returns:
        A new list of every user record, in USERS order.
    """
    return list(USERS.values())

def get_notification_pref(user_id: int) -> str | None:
    """Retrieve a user's notification preference.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The user's notification preference, or None if no preference is set.

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    return get_user(user_id)["notification_pref"]

def set_notification_pref(user_id: int, notification_pref: str | None) -> dict:
    """Set a user's notification preference.

    Args:
        user_id: The unique identifier for the user.
        notification_pref: One of NOTIFICATION_PREFS, or None to reset the
            preference to the default.

    Returns:
        The updated user record.

    Raises:
        NotFoundError: If no user exists with the given ID.
        ValidationError: If notification_pref is not None or one of
            NOTIFICATION_PREFS.
    """
    user = get_user(user_id)
    if notification_pref is None:
        notification_pref = DEFAULT_NOTIFICATION_PREF
    elif not isinstance(notification_pref, str) or notification_pref not in NOTIFICATION_PREFS:
        raise ValidationError("notification_pref", "must be one of email, sms, none, or null")
    user["notification_pref"] = notification_pref
    return user
