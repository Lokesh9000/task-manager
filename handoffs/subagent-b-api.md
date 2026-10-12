# Subagent B handoff: API integration

Only `routes/api.py` was modified. Nothing was committed or pushed.

## New routes

All three are on the existing `api` blueprint, mounted at `/api`. Errors reach the client through
the existing `@api.errorhandler(AppError)` as `{"error": "<message>"}`; the routes do no
validation or user lookup of their own.

### `GET /api/users`

- Route function: `list_users_route()`
- Request body: none
- Success: 200, bare JSON array of user records in `USERS` insertion order, each with `id`,
  `name`, `email`, `notification_pref`. The body is `jsonify(list_users())`.
- Errors: none

### `GET /api/users/<int:user_id>/notifications`

- Route function: `get_notification_pref_route(user_id)`
- Request body: none
- Success: 200, `{"notification_pref": "<value>"}`; `{"notification_pref": "none"}` on seeded data
- Errors:

| Condition | Status | Body |
|---|---|---|
| unknown `user_id` | 404 | `{"error": "User not found"}` |

### `PATCH /api/users/<int:user_id>/notifications`

- Route function: `update_notification_pref_route(user_id)`
- Request body: JSON object `{"notification_pref": "<value>"}`, where the value is exactly
  `"email"`, `"sms"` or `"none"`. `request.get_json()` is passed straight to
  `update_notification_pref`.
- Success: 200, `{"notification_pref": "<value>"}` taken from the updated record the service
  returns (only this field is returned, not the whole user record)
- Errors, in the order the service checks them:

| Condition | Status | Body |
|---|---|---|
| unknown `user_id` | 404 | `{"error": "User not found"}` |
| body is a JSON array or JSON `null` | 422 | `{"error": "Invalid request: must be a JSON object"}` |
| any field other than `notification_pref` | 422 | `{"error": "Invalid request: only notification_pref can be updated"}` |
| `{}` | 422 | `{"error": "Invalid notification_pref: is required"}` |
| value not exactly `"email"`, `"sms"` or `"none"` | 422 | `{"error": "Invalid notification_pref: must be one of: email, sms, none"}` |

Behaviour for a non-JSON content type or malformed JSON is not defined by the contract and was
not changed or handled in the route; it is whatever Flask's `request.get_json()` does.

## Existing code left untouched

- `@api.errorhandler(AppError)` / `handle_app_error`
- `GET /api/tasks/<int:task_id>`
- `PATCH /api/tasks/<int:task_id>`
- `GET /api/tasks`
- `POST /api/tasks`
- `GET /api/users/<int:user_id>` (its response now includes `notification_pref` because the
  stored record does)

The only edit above the new routes is the import line, which changed from
`from services.users import get_user` to
`from services.users import get_user, list_users, get_notification_pref, update_notification_pref`.
The import block was not reordered and the unused `process_order` import is still there.

## Verification output

### 1. `.venv/Scripts/python -m pytest -q`

```
127 passed in 0.24s
```

### 2. `.venv/Scripts/python -m ruff check .`

Run with `--output-format concise` added. 5 findings, the same as the baseline, no new one:

```
app.py:1:1: I001 [*] Import block is un-sorted or un-formatted
routes\api.py:1:1: I001 [*] Import block is un-sorted or un-formatted
routes\api.py:2:51: F401 [*] `services.tasks.process_order` imported but unused
tests\test_tasks.py:1:1: I001 [*] Import block is un-sorted or un-formatted
tests\test_tasks.py:25:10: B017 Do not assert blind exception: `Exception`
Found 5 errors.
[*] 4 fixable with the `--fix` option.
```

### 3. Smoke check

The command from the prompt printed:

```
[{'email': 'alice@example.com', 'id': 1, 'name': 'Alice', 'notification_pref': 'none'}, {'email': 'bob@example.com', 'id': 2, 'name': 'Bob', 'notification_pref': 'none'}]
{'email': 'alice@example.com', 'id': 1, 'name': 'Alice', 'notification_pref': 'none'}
{'notification_pref': 'none'}
200 {'notification_pref': 'email'}
422 {'error': 'Invalid notification_pref: must be one of: email, sms, none'}
404 {'error': 'User not found'}
```

(Keys print alphabetically because Flask's JSON provider sorts keys by default.)

A second one-off `python -c` command (fresh process, no file written) covered the remaining
cases from the prompt's expected behaviour, plus two existing routes:

```
GET /api/users -> 200 [{'email': 'alice@example.com', 'id': 1, 'name': 'Alice', 'notification_pref': 'none'}, {'email': 'bob@example.com', 'id': 2, 'name': 'Bob', 'notification_pref': 'none'}]
PATCH {} -> 422 {'error': 'Invalid notification_pref: is required'}
PATCH extra field -> 422 {'error': 'Invalid request: only notification_pref can be updated'}
PATCH array -> 422 {'error': 'Invalid request: must be a JSON object'}
PATCH null -> 422 {'error': 'Invalid request: must be a JSON object'}
PATCH 999 -> 404 {'error': 'User not found'}
GET /api/users/1/notifications after rejects -> 200 {'notification_pref': 'none'}
GET /api/users/999 -> 404 {'error': 'User not found'}
GET /api/tasks/1 -> 200 {'done': False, 'id': 1, 'priority': 3, 'title': 'Buy groceries', 'user_id': 1}
```

The extra-field body was `{"notification_pref": "sms", "name": "x"}`; the null body was sent as
`data="null", content_type="application/json"`.

### 4. `git status --short`

```
 M routes/api.py
 M services/users.py
?? DECOMPOSITION.md
?? handoffs/
```

`DECOMPOSITION.md` was already untracked before this session and was not edited. Git shows the
handoff files as their directory, `handoffs/`, which now contains `subagent-a-service.md`
(Subagent A's, not edited) and this file. `git diff --stat -- routes/api.py` reports 14
insertions and 1 deletion.

## Differences from the agreed contract

No difference from the agreed contract.
