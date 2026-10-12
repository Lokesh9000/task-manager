# Subagent A handoff: user service

Only `services/users.py` was modified. Nothing was committed or pushed.

## Public names in `services/users.py`

| Name | Signature / value | Returns | Status |
|---|---|---|---|
| `NOTIFICATION_PREFS` | `("email", "sms", "none")` | tuple of allowed values | added |
| `DEFAULT_NOTIFICATION_PREF` | `"none"` | default value | added |
| `USERS` | `dict[int, dict]` | both seed records gain `"notification_pref": "none"`; ids, names, emails unchanged | changed (data only) |
| `get_user` | `get_user(user_id: int) -> dict` | the stored user record, which now includes `notification_pref` | not edited |
| `create_user` | `create_user(name: str, email: str) -> dict` | the new stored record, now including `"notification_pref": "none"`; existing validation unchanged | changed (record contents only) |
| `list_users` | `list_users() -> list[dict]` | a new list of every user record in `USERS` insertion order; the records themselves are the stored dictionaries, not copies | added |
| `get_notification_pref` | `get_notification_pref(user_id: int) -> str` | the stored preference string | added |
| `update_notification_pref` | `update_notification_pref(user_id: int, updates: object) -> dict` | the updated stored user record (all fields, not just the preference) | added |

Private helper, not for use by routes: `_validate_notification_pref(value: object) -> str`.

## Validation rules

Allowed values are exactly the `str` values `"email"`, `"sms"`, `"none"`. Nothing is stripped,
lowercased or coerced. The type is checked first (`type(value) is not str`), so lists and dicts
raise `ValidationError`, not `TypeError`.

`get_notification_pref(user_id)`:

| Condition | Error | Status | Message |
|---|---|---|---|
| unknown `user_id` | `NotFoundError("User")` | 404 | `User not found` |

`update_notification_pref(user_id, updates)` checks in this order:

| # | Condition | Error | Status | Message |
|---|---|---|---|---|
| a | unknown `user_id` | `NotFoundError("User")` | 404 | `User not found` |
| b | `type(updates) is not dict` | `ValidationError("request", ...)` | 422 | `Invalid request: must be a JSON object` |
| c | any key other than `notification_pref` | `ValidationError("request", ...)` | 422 | `Invalid request: only notification_pref can be updated` |
| d | `notification_pref` key missing | `ValidationError("notification_pref", ...)` | 422 | `Invalid notification_pref: is required` |
| e | value not exactly `"email"`, `"sms"` or `"none"` | `ValidationError("notification_pref", ...)` | 422 | `Invalid notification_pref: must be one of: email, sms, none` |

The value is stored only after every check passes, so a rejected call leaves `USERS` unchanged.
An unknown user wins over an invalid body (`update_notification_pref(999, None)` raises
`NotFoundError`).

## Verification output

### 1. `.venv/Scripts/python -m pytest -q`

```
127 passed in 0.28s
```

### 2. `.venv/Scripts/python -m ruff check .`

5 findings, the same as the baseline, none in `services/users.py`:

```
app.py:1:1: I001 [*] Import block is un-sorted or un-formatted
routes\api.py:1:1: I001 [*] Import block is un-sorted or un-formatted
routes\api.py:2:51: F401 [*] `services.tasks.process_order` imported but unused
tests\test_tasks.py:1:1: I001 [*] Import block is un-sorted or un-formatted
tests\test_tasks.py:25:10: B017 Do not assert blind exception: `Exception`
Found 5 errors.
```

### 3. Smoke check

The command from the prompt printed:

```
[{'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'notification_pref': 'none'}, {'id': 2, 'name': 'Bob', 'email': 'bob@example.com', 'notification_pref': 'none'}]
none
{'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'notification_pref': 'sms'}
sms
```

A second one-off `python -c` command (fresh process, no file written) called
`update_notification_pref` with each rejected input, then compared `USERS` with a deep copy
taken beforehand, then called `create_user`:

```
1 {'notification_pref': None} -> ValidationError 422 Invalid notification_pref: must be one of: email, sms, none
1 {'notification_pref': ''} -> ValidationError 422 Invalid notification_pref: must be one of: email, sms, none
1 {'notification_pref': 'push'} -> ValidationError 422 Invalid notification_pref: must be one of: email, sms, none
1 {'notification_pref': 'EMAIL'} -> ValidationError 422 Invalid notification_pref: must be one of: email, sms, none
1 {'notification_pref': ' email'} -> ValidationError 422 Invalid notification_pref: must be one of: email, sms, none
1 {'notification_pref': 'email '} -> ValidationError 422 Invalid notification_pref: must be one of: email, sms, none
1 {'notification_pref': 1} -> ValidationError 422 Invalid notification_pref: must be one of: email, sms, none
1 {'notification_pref': True} -> ValidationError 422 Invalid notification_pref: must be one of: email, sms, none
1 {'notification_pref': ['email']} -> ValidationError 422 Invalid notification_pref: must be one of: email, sms, none
1 {'notification_pref': {'a': 1}} -> ValidationError 422 Invalid notification_pref: must be one of: email, sms, none
1 {} -> ValidationError 422 Invalid notification_pref: is required
1 {'name': 'x'} -> ValidationError 422 Invalid request: only notification_pref can be updated
1 {'notification_pref': 'sms', 'name': 'x'} -> ValidationError 422 Invalid request: only notification_pref can be updated
1 [] -> ValidationError 422 Invalid request: must be a JSON object
1 None -> ValidationError 422 Invalid request: must be a JSON object
999 {'notification_pref': 'sms'} -> NotFoundError 404 User not found
999 None -> NotFoundError 404 User not found
get 999 -> NotFoundError 404 User not found
USERS unchanged: True
{'id': 3, 'name': 'Cara', 'email': 'cara@example.com', 'notification_pref': 'none'}
```

### 4. `git status --short`

```
 M services/users.py
?? DECOMPOSITION.md
?? handoffs/
```

`DECOMPOSITION.md` was already untracked before this session started and was not edited. The
prompt expected only `services/users.py` and the handoff file to appear; the extra
`DECOMPOSITION.md` line is that pre-existing untracked file. Git shows the new handoff as its
directory, `handoffs/`, which contains only `subagent-a-service.md`.

## Differences from the agreed contract

No difference from the agreed contract.
