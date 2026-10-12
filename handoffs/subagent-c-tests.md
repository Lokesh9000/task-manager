# Subagent C handoff: tests

Only `tests/test_notifications.py` was created, plus this file. No other file was modified.
Nothing was committed or pushed. No `conftest.py` was created.

## Test results

`.venv/Scripts/python -m pytest -q`:

```
183 passed in 0.30s
```

127 existing tests in `tests/test_tasks.py` plus 56 new test cases in
`tests/test_notifications.py`, from 20 test functions:

| Level | Test functions | Test cases |
|---|---|---|
| Service | 11 | 31 |
| API | 9 | 25 |
| Total | 20 | 56 |

The split was confirmed with `pytest -q tests/test_notifications.py -k "not api"` (31 passed) and
`-k "api"` (25 passed). Every new test passed on the first run; no test was changed to get a
green run.

## Fixtures

Both are defined inside `tests/test_notifications.py`:

- `restore_users`: deep-copies `USERS`, then in a `finally` block clears `USERS` and restores the
  snapshot (same pattern as `restore_tasks`). Every test in the file requests it.
- `client`: `app.test_client()`.

## Coverage summary

Service level:

| Test function | Cases | Behaviour covered |
|---|---|---|
| `test_seed_users_have_default_notification_pref` | 1 | Both seeded users have `notification_pref` `"none"`. |
| `test_create_user_default_notification_pref` | 1 | `create_user` returns and stores a record with `notification_pref` `"none"`. |
| `test_list_users_returns_every_user_with_notification_pref` | 1 | `list_users` returns every stored record in insertion order, each with its `notification_pref`. |
| `test_list_users_returns_new_list` | 1 | `list_users` returns a new list each call; clearing it does not change `USERS`. |
| `test_get_user_includes_notification_pref` | 1 | `get_user` returns a record that includes `notification_pref`. |
| `test_get_notification_pref_valid` | 1 | `get_notification_pref` returns the stored value (default and a changed one). |
| `test_get_notification_pref_unknown_user` | 1 | `get_notification_pref` raises `NotFoundError` (404, `User not found`) for an unknown user. |
| `test_update_notification_pref_valid` | 3 | `"email"`, `"sms"`, `"none"`: returns the updated record, stores the value, leaves the other user unchanged. The stored value is first set to something different so each case is a real change. |
| `test_update_notification_pref_invalid_value` | 10 | `None`, `""`, `"push"`, `"EMAIL"`, `" email"`, `"email "`, `1`, `True`, `["email"]`, `{"a": 1}`: `ValidationError` 422 with `Invalid notification_pref: must be one of: email, sms, none`; `USERS` equals the earlier deep copy. |
| `test_update_notification_pref_invalid_updates` | 5 | `{}` (is required), unknown key and valid key plus extra key (only notification_pref can be updated), `[]` and `None` (must be a JSON object); `USERS` unchanged. |
| `test_update_notification_pref_unknown_user` | 6 | Unknown user raises `NotFoundError` (404) for a valid body and for invalid bodies (bad value, unknown key, `{}`, `[]`, `None`); `USERS` unchanged. |

API level:

| Test function | Cases | Behaviour covered |
|---|---|---|
| `test_api_list_users` | 1 | `GET /api/users` -> 200, body equals the list of stored records, each with `notification_pref`. |
| `test_api_get_user_includes_notification_pref` | 1 | `GET /api/users/1` -> 200, body includes `notification_pref`. |
| `test_api_get_notification_pref` | 1 | `GET /api/users/1/notifications` -> 200 `{"notification_pref": "none"}`. |
| `test_api_get_notification_pref_unknown_user` | 1 | `GET /api/users/999/notifications` -> 404 `{"error": "User not found"}`. |
| `test_api_update_notification_pref_valid` | 3 | `PATCH` with each valid value -> 200 `{"notification_pref": value}`; following `GET` of `/notifications`, `/api/users/1` and `/api/users` reflects the change; user 2 unchanged. |
| `test_api_update_notification_pref_invalid_value` | 10 | `PATCH` with the same ten invalid values (all are JSON-representable) -> 422 with the exact error body; `USERS` unchanged. |
| `test_api_update_notification_pref_invalid_body` | 5 | `PATCH` with `{}`, an unknown field, a valid field plus an extra field, and JSON arrays `[]` and `["email"]` -> 422 with the matching message; `USERS` unchanged. |
| `test_api_update_notification_pref_null_body` | 1 | `PATCH` with a literal JSON `null` body (`data="null"`, `content_type="application/json"`) -> 422 `Invalid request: must be a JSON object`; `USERS` unchanged. |
| `test_api_update_notification_pref_unknown_user` | 2 | `PATCH /api/users/999/notifications` -> 404 `{"error": "User not found"}` for a valid and an invalid value; `USERS` unchanged. |

Not tested, because the contract does not define it: non-JSON content types and malformed JSON.

## Ruff output

`.venv/Scripts/python -m ruff check . --output-format concise` (the same 5 baseline findings,
none in `tests/test_notifications.py`):

```
app.py:1:1: I001 [*] Import block is un-sorted or un-formatted
routes\api.py:1:1: I001 [*] Import block is un-sorted or un-formatted
routes\api.py:2:51: F401 [*] `services.tasks.process_order` imported but unused
tests\test_tasks.py:1:1: I001 [*] Import block is un-sorted or un-formatted
tests\test_tasks.py:25:10: B017 Do not assert blind exception: `Exception`
Found 5 errors.
[*] 4 fixable with the `--fix` option.
```

## `git status --short`

```
 M routes/api.py
 M services/users.py
?? DECOMPOSITION.md
?? handoffs/
?? tests/test_notifications.py
```

`handoffs/subagent-c-tests.md` does not appear on its own line because Git shows the untracked
`handoffs/` directory as a single entry; that directory holds the three handoff files.
`DECOMPOSITION.md` was already untracked before this session and was not edited.

## Defects, disagreements and gaps

No defects or gaps found.

Both handoff files state "No difference from the agreed contract", and the tests, written against
the contract in `DECOMPOSITION.md`, agree: no disagreement between the handoffs and the contract
was found.
