from utils.errors import NotFoundError, ValidationError

NOTIFICATION_PREFS = ("email", "sms", "none")
DEFAULT_NOTIFICATION_PREF = "none"

USERS: dict[int, dict] = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com", "notification_pref": "none"},
    2: {"id": 2, "name": "Bob",   "email": "bob@example.com",   "notification_pref": "none"},
}

def _validate_notification_pref(value: object) -> str:
    """Validate a notification preference.

    Args:
        value: The candidate notification preference.

    Returns:
        The validated notification preference.

    Raises:
        ValidationError: If value is not exactly one of the strings "email",
            "sms", or "none". Values are not stripped or lowercased, and
            None, numbers, booleans, lists, and dicts are rejected.
    """
    if type(value) is not str or value not in NOTIFICATION_PREFS:
        raise ValidationError("notification_pref", "must be one of: email, sms, none")
    return value

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
        The newly created user record. Its notification preference is set
        to the default, "none".

    Raises:
        ValidationError: If name or email is empty.
    """
    if not name or not name.strip():
        raise ValidationError("name", "cannot be empty")
    if not email or "@" not in email:
        raise ValidationError("email", "must be a valid email address")
    new_id = max(USERS.keys()) + 1
    USERS[new_id] = {"id": new_id, "name": name, "email": email,
                     "notification_pref": DEFAULT_NOTIFICATION_PREF}
    return USERS[new_id]

def list_users() -> list[dict]:
    """Retrieve all users.

    Returns:
        A new list of every user record, in insertion order.
    """
    return list(USERS.values())

def get_notification_pref(user_id: int) -> str:
    """Retrieve the notification preference of a user.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The stored notification preference: "email", "sms", or "none".

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    return get_user(user_id)["notification_pref"]

def update_notification_pref(user_id: int, updates: object) -> dict:
    """Update the notification preference of an existing user.

    Args:
        user_id: The unique identifier for the user.
        updates: The requested changes. Must be a dictionary containing
            only the key "notification_pref".

    Returns:
        The updated user record as a dictionary.

    Raises:
        NotFoundError: If no user exists with the given ID.
        ValidationError: If updates is not a dictionary, contains a field
            other than notification_pref, omits notification_pref, or
            notification_pref is not one of "email", "sms", or "none".
    """
    user = get_user(user_id)
    if type(updates) is not dict:
        raise ValidationError("request", "must be a JSON object")
    if any(field != "notification_pref" for field in updates):
        raise ValidationError("request", "only notification_pref can be updated")
    if "notification_pref" not in updates:
        raise ValidationError("notification_pref", "is required")
    user["notification_pref"] = _validate_notification_pref(updates["notification_pref"])
    return user
