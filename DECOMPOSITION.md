# PA 5, Task 2 — Subagent Pipeline: User Notification Preference

- **Finalized:** 2026-10-12, before any implementation subagent started. It was drafted with Claude Code in a preparation session that changed no implementation files.
- **Base commit:** `b089889` (PA5 Task 1 Session 4: add priority filtering)
- **Status:** No subagent has run yet. Every result below is a placeholder until it is recorded from an actual run.

## Baseline

Measured at `b089889` with a clean working tree:

| Check | Command | Result |
|---|---|---|
| Tests | `.venv/Scripts/python -m pytest -q` | 119 passed |
| Lint | `.venv/Scripts/python -m ruff check .` | 5 pre-existing findings |

The 5 Ruff findings are `app.py:1` I001, `routes/api.py:1` I001, `routes/api.py:2` F401, `tests/test_tasks.py:1` I001 and `tests/test_tasks.py:20` B017. None is in `services/users.py` or `tests/test_api.py`.

## Feature contract

From the assignment:

- A user can set a notification preference: `email`, `sms`, or `none` (default: `none`).
- The preference is stored on the User model (new nullable column: `notification_pref`).
- `PATCH /users/{id}/notifications` updates the preference and rejects invalid values with `ValidationError`.
- `GET /users/{id}/notifications` returns the current preference.
- The user list and user detail endpoints must include `notification_pref` in their response.

Design decisions, made where the assignment does not specify behavior:

| Topic | Decision |
|---|---|
| Allowed preferences | `"email"`, `"sms"`, `"none"` (exact, case-sensitive strings) |
| Default stored value | Python `None` / JSON `null` |
| Meaning of `"none"` | An explicit choice: notifications disabled. It is distinct from the unset default `null`. |
| PATCH with JSON `null` | Resets the preference to the default |
| PATCH body | `{"notification_pref": "email"}` |
| PATCH success | HTTP 200 with the updated user object |
| `GET /api/users/<id>/notifications` | Returns `{"notification_pref": value}` |
| `GET /api/users` | New endpoint; returns the user records, each including `notification_pref`. No user list endpoint existed before this task. |
| `GET /api/users/<id>` | Existing endpoint; includes `notification_pref` |
| Invalid values | Raise the existing `ValidationError` (HTTP 422 through the existing `AppError` handler) |

Supporting details the prompts depend on, also design decisions:

| Topic | Decision |
|---|---|
| Invalid-value message | `Invalid notification_pref: must be one of email, sms, none, or null` |
| PATCH body without a `notification_pref` key | 422 `Invalid notification_pref: is required` |
| PATCH body that is not a JSON object | 422 `Invalid request body: must be a JSON object` |
| Unknown user ID | 404 `User not found`, from the existing `NotFoundError` |
| Validation order for PATCH | Body is an object (422), key present (422), user exists (404), value valid (422), then assign. This is the same order as the existing `PATCH /api/tasks/<id>`. |
| Route file | `routes/api.py`, as `CLAUDE.md` requires. No new route module. |

## Execution rules

- The four subagents run in order: SA-1, SA-2, SA-3, SA-4. Each depends on the one before it.
- Each subagent runs in a fresh Claude Code session (`/clear` or relaunch), with no carried-over context.
- Each prompt below is issued verbatim.
- After each subagent, `pytest -q` is run and the actual result is recorded in that subagent's Result row.
- A failing test is fixed in the same session and the fix is noted in the Result row. A red state is not carried forward.
- If a fix would require a file outside the subagent's Output field, the subagent stops and reports instead of editing it. Any such fix is then authorized in that same session and recorded under Divergence.
- `git status --short` and `git diff --stat` are captured before and after each subagent, and the two are compared to check that session's changes against its Constraint field. The final status alone is not enough, because earlier subagents may have uncommitted changes.
- SA-2 edits `services/users.py`, which SA-1 will already have modified, so a status comparison cannot separate the two. For SA-2 the complete `git diff -- services/users.py` is captured before and after, and the two diffs are compared to identify only SA-2's changes and to confirm SA-1's were preserved.

## Subagent table

| Subagent # | Output | Depends on |
|---|---|---|
| SA-1: Data layer | `services/users.py` | Baseline |
| SA-2: Service layer | `services/users.py` | SA-1 |
| SA-3: API layer | `routes/api.py` | SA-2 |
| SA-4: Tests | `tests/test_users.py` (new), `tests/test_api.py` | SA-1, SA-2, SA-3 |

### SA-1: Data layer

| Field | Value |
|---|---|
| **Subagent #** | SA-1: Data layer |
| **Input** | `services/users.py` |
| **Task** | Add the `notification_pref` field, with a default of `None`, to every user record and define the constants for the allowed values and the default. |
| **Output** | Modifies `services/users.py` only. |
| **Result (`pytest -q`) and fixes** | _TO BE RECORDED after SA-1 runs: actual `pytest -q` result, Ruff result, files changed, and any fix made._ |
| **Constraint** | Must not add any function or change the signature, validation or docstring of `get_user()` or `create_user()`. Must not touch `routes/api.py`, `services/tasks.py`, `utils/errors.py`, `app.py`, `requirements.txt`, `tests/test_tasks.py`, `tests/test_api.py`, `CLAUDE.md`, `PLAN_LOG.md` or `DECOMPOSITION.md`. Must not create any file. |
| **Hand-off** | In `services/users.py`: the key `notification_pref` on both seed users and on records built by `create_user()`; `NOTIFICATION_PREFS = ("email", "sms", "none")`; `DEFAULT_NOTIFICATION_PREF = None`. |

Prompt for SA-1:

```text
You are SA-1 (Data layer) in a four-step pipeline that adds a user notification preference to this Flask task-manager project. Do only the data-layer step described here.

Read first: services/users.py

Task: add a notification_pref field to the user records in services/users.py.

Make exactly these changes, all in services/users.py:
1. Below the imports and above USERS, add two module-level constants:
   NOTIFICATION_PREFS: tuple[str, ...] = ("email", "sms", "none")
   DEFAULT_NOTIFICATION_PREF = None
2. Add "notification_pref": None to both seed records in USERS (ids 1 and 2).
3. In create_user(), include "notification_pref": DEFAULT_NOTIFICATION_PREF in the record it stores, so new users get the default.

Meaning of the values, for context: None is the default (no preference set, JSON null). "none" is an explicit choice meaning notifications are disabled.

Constraints:
- Modify services/users.py only.
- Do not add any new function. Do not change the signature, validation, or docstring of get_user() or create_user().
- Do not move USERS out of services/users.py.
- Do not touch routes/api.py, services/tasks.py, utils/errors.py, app.py, requirements.txt, tests/test_tasks.py, tests/test_api.py, CLAUDE.md, PLAN_LOG.md, or DECOMPOSITION.md.
- Do not create any new file. Do not commit or push.
- DECOMPOSITION.md may show as untracked or modified. Leave it alone.

Verification:
1. Run: .venv/Scripts/python -m pytest -q
   Expected: 119 passed. This is the baseline; this step adds no tests.
2. Run: .venv/Scripts/python -m ruff check .
   Expected: Found 5 errors. These are pre-existing findings in app.py, routes/api.py and tests/test_tasks.py. Do not fix them, and do not introduce any new one.
3. Run: git status --short and git diff --stat
   Expected: services/users.py is the only file you changed.

If a test fails, fix it in this session by changing services/users.py only. If the fix would need any other file, stop and tell me instead of editing it.

Report: the final constants and USERS definition, the exact pytest and Ruff result lines, and the list of files you changed.
```

### SA-2: Service layer

| Field | Value |
|---|---|
| **Subagent #** | SA-2: Service layer |
| **Input** | `services/users.py`, `utils/errors.py` |
| **Task** | Add the service functions that list users and that get and set a user's notification preference, with validation. |
| **Output** | Modifies `services/users.py` only. |
| **Result (`pytest -q`) and fixes** | _TO BE RECORDED after SA-2 runs: actual `pytest -q` result, Ruff result, the before-edit and after-edit `git diff -- services/users.py`, the functions or lines SA-2 added or modified, whether SA-1's field, defaults and constants were preserved, and any fix made._ |
| **Constraint** | Must preserve SA-1's data changes in `services/users.py`: the `USERS` seed records, `NOTIFICATION_PREFS`, `DEFAULT_NOTIFICATION_PREF`, and the existing `get_user()` and `create_user()`. Must not touch `routes/api.py`, `services/tasks.py`, `utils/errors.py`, `app.py`, `requirements.txt`, `tests/test_tasks.py`, `tests/test_api.py`, `CLAUDE.md`, `PLAN_LOG.md` or `DECOMPOSITION.md`. Must not create any file. |
| **Hand-off** | In `services/users.py`: `list_users() -> list[dict]`; `get_notification_pref(user_id: int) -> str \| None`; `set_notification_pref(user_id: int, notification_pref: str \| None) -> dict`, which returns the updated user record. Errors: `NotFoundError("User")` and `ValidationError("notification_pref", "must be one of email, sms, none, or null")`. |

Prompt for SA-2:

```text
You are SA-2 (Service layer) in a four-step pipeline that adds a user notification preference to this Flask task-manager project. SA-1 has already added the data. Do only the service-layer step described here.

Read first: services/users.py and utils/errors.py

Precondition: services/users.py must already contain NOTIFICATION_PREFS = ("email", "sms", "none"), DEFAULT_NOTIFICATION_PREF = None, a "notification_pref" key in both seed records in USERS, and the same key in the record create_user() stores. If any of these is missing, stop and tell me. Do not add it yourself.

Before you edit anything, record the before-edit baseline:
1. Run: git status --short
2. Run: git diff -- services/users.py
3. Keep the complete output of both. Do not save it to a file in the repository; you will paste it into your report.
services/users.py is expected to show as modified already, and the diff is expected to contain SA-1's changes. If SA-1's changes were already committed, the diff will be empty; say so in your report.

Task: add three service functions to services/users.py, after create_user().

1. list_users() -> list[dict]
   Returns a new list of every user record, in USERS order. It must not modify USERS.

2. get_notification_pref(user_id: int) -> str | None
   Looks the user up with get_user() and returns that user's notification_pref value.
   Raises NotFoundError if the user does not exist.

3. set_notification_pref(user_id: int, notification_pref: str | None) -> dict
   - First looks the user up with get_user(), so an unknown user raises NotFoundError even when the value is also invalid.
   - Then validates the value. It is valid only if it is None or exactly one of the strings in NOTIFICATION_PREFS (case-sensitive). Any other value, including "Email", "", 1, True, [] and {}, must raise:
     ValidationError("notification_pref", "must be one of email, sms, none, or null")
     which produces the message "Invalid notification_pref: must be one of email, sms, none, or null".
   - None resets the preference: store DEFAULT_NOTIFICATION_PREF.
   - Assign only after both checks pass, so a rejected call leaves USERS unchanged.
   - Returns the updated user record.

Meaning of the values, for context: None is the default (no preference set, JSON null). "none" is an explicit choice meaning notifications are disabled.

Style: follow get_user() and create_user() in services/users.py. Every new function needs parameter and return type hints and a Google-style docstring with Args, Returns and Raises sections where they apply. Use NotFoundError and ValidationError from utils/errors.py.

Constraints:
- Modify services/users.py only.
- Preserve SA-1's work: do not change the USERS seed records, NOTIFICATION_PREFS, DEFAULT_NOTIFICATION_PREF, get_user(), or create_user().
- Do not move USERS out of services/users.py.
- Do not touch routes/api.py, services/tasks.py, utils/errors.py, app.py, requirements.txt, tests/test_tasks.py, tests/test_api.py, CLAUDE.md, PLAN_LOG.md, or DECOMPOSITION.md.
- Do not add routes or tests. Do not create any new file. Do not commit or push.
- Other files may already show as modified or untracked from earlier pipeline steps. Do not touch or revert them.

Verification:
1. Run: .venv/Scripts/python -m pytest -q
   Expected: 119 passed. This step adds no tests.
2. Run: .venv/Scripts/python -m ruff check .
   Expected: Found 5 errors. These are pre-existing findings in app.py, routes/api.py and tests/test_tasks.py. Do not fix them, and do not introduce any new one.
3. Run: git status --short
   Expected: identical to the before-edit output. services/users.py is the only file this session changed, and it was already listed as modified.
4. Run: git diff -- services/users.py
5. Compare the complete before-edit and after-edit diffs of services/users.py. Everything in the before-edit diff is SA-1's work; only what is new in the after-edit diff is yours.
   Expected: the only new content is the three functions list_users(), get_notification_pref() and set_notification_pref(), plus any import they need.
6. Confirm SA-1's work is preserved: every line of the before-edit diff must still appear unchanged in the after-edit diff. That covers the "notification_pref": None field on both seed users, the default in create_user(), NOTIFICATION_PREFS and DEFAULT_NOTIFICATION_PREF.

If a test fails, fix it in this session by changing services/users.py only. If the fix would need any other file, stop and tell me instead of editing it.

Report:
- The exact pytest and Ruff result lines.
- The complete before-edit and after-edit output of git status --short and of git diff -- services/users.py.
- The specific functions or lines this session added or modified in services/users.py, with the three function signatures as written.
- An explicit confirmation that SA-1's notification_pref field, defaults and constants were preserved, or a list of exactly what changed if not.
```

### SA-3: API layer

| Field | Value |
|---|---|
| **Subagent #** | SA-3: API layer |
| **Input** | `routes/api.py`, `services/users.py`, `utils/errors.py` |
| **Task** | Add the user list route and the GET and PATCH notification routes, each calling the service functions from SA-2. |
| **Output** | Modifies `routes/api.py` only. |
| **Result (`pytest -q`) and fixes** | _TO BE RECORDED after SA-3 runs: actual `pytest -q` result, Ruff result, files changed, and any fix made._ |
| **Constraint** | Must not touch `services/users.py`, `services/tasks.py` or `utils/errors.py`. Must not change `handle_app_error` or any existing route in `routes/api.py`. Must not read or write `USERS` directly from `routes/api.py`. Must not touch `app.py`, `requirements.txt`, `tests/test_tasks.py`, `tests/test_api.py`, `CLAUDE.md`, `PLAN_LOG.md` or `DECOMPOSITION.md`. Must not create any file, including `routes/users.py`. |
| **Hand-off** | Routes under the `/api` prefix: `GET /api/users` (200, list of user records); `GET /api/users/<id>/notifications` (200, `{"notification_pref": value}`); `PATCH /api/users/<id>/notifications` (200, updated user record). Error bodies are `{"error": message}` with status 422 or 404, as listed in the feature contract. |

Prompt for SA-3:

```text
You are SA-3 (API layer) in a four-step pipeline that adds a user notification preference to this Flask task-manager project. SA-1 added the data and SA-2 added the service functions. Do only the API-layer step described here.

Read first: routes/api.py, services/users.py and utils/errors.py

Precondition: services/users.py must already define list_users(), get_notification_pref(user_id) and set_notification_pref(user_id, notification_pref). If any of these is missing, stop and tell me. Do not add or change anything in services/users.py yourself.

Before you edit anything: run git status --short and git diff --stat and keep the output. SA-1 and SA-2 may have left uncommitted changes, so services/users.py is expected to show as modified already. Those changes are expected. Do not modify or revert them, and do not report them as yours.

Task: add three routes to routes/api.py, after the existing get_user_route. The blueprint is registered under /api, so the full paths are shown in brackets.

1. GET /users  [GET /api/users]
   Returns 200 with jsonify(list_users()).

2. GET /users/<int:user_id>/notifications  [GET /api/users/<id>/notifications]
   Returns 200 with {"notification_pref": value}, where value comes from get_notification_pref(user_id). The value is null, "email", "sms" or "none".

3. PATCH /users/<int:user_id>/notifications  [PATCH /api/users/<id>/notifications]
   Request body: a JSON object such as {"notification_pref": "email"}. JSON null is a valid value and resets the preference.
   Checks, in this order:
   a. If the parsed body is not a JSON object (dict), raise ValidationError("request body", "must be a JSON object").
   b. If the body has no "notification_pref" key, raise ValidationError("notification_pref", "is required"). Test for the key itself, not for a truthy value, because null is valid.
   c. Call set_notification_pref(user_id, data["notification_pref"]). The service raises NotFoundError for an unknown user and ValidationError for an invalid value.
   Returns 200 with the updated user record returned by the service.

Follow the existing update_task_route in routes/api.py for the body checks and style. Extend the existing import from services.users. The existing @api.errorhandler(AppError) already converts ValidationError to 422 and NotFoundError to 404 as {"error": message}; rely on it and add no other error handling. The existing GET /users/<int:user_id> route needs no change.

Constraints:
- Modify routes/api.py only.
- Do not validate preference values in the route and do not read or write USERS from routes/api.py. All user logic stays in services/users.py.
- Do not change handle_app_error or any existing route.
- Do not touch services/users.py, services/tasks.py, utils/errors.py, app.py, requirements.txt, tests/test_tasks.py, tests/test_api.py, CLAUDE.md, PLAN_LOG.md, or DECOMPOSITION.md.
- Do not add tests. Do not create any new file, including routes/users.py. Do not commit or push.
- Other files may already show as modified or untracked from earlier pipeline steps. Do not touch or revert them.

Verification:
1. Run: .venv/Scripts/python -m pytest -q
   Expected: 119 passed. This step adds no tests.
2. Run: .venv/Scripts/python -m ruff check .
   Expected: Found 5 errors. These are pre-existing findings in app.py, routes/api.py and tests/test_tasks.py, including two already in routes/api.py (I001 unsorted imports and F401 unused process_order). Do not fix them, and do not introduce any new one.
3. Run: git status --short and git diff --stat again, and compare with the output you recorded before editing.
   Expected: routes/api.py is the only difference between the two. Anything that already appeared before you started belongs to SA-1 or SA-2, not to this session.

If a test fails, fix it in this session by changing routes/api.py only. If the fix would need any other file, stop and tell me instead of editing it.

Report: the three route functions as written, the exact pytest and Ruff result lines, the before and after git status --short output, and the files that changed during this session.
```

### SA-4: Tests

| Field | Value |
|---|---|
| **Subagent #** | SA-4: Tests |
| **Input** | `services/users.py`, `routes/api.py`, `utils/errors.py`, `tests/test_api.py`, `tests/test_tasks.py` |
| **Task** | Add isolated service tests and API tests that verify the notification preference feature against the feature contract. |
| **Output** | Creates `tests/test_users.py`. Modifies `tests/test_api.py` by addition only. |
| **Result (`pytest -q`) and fixes** | _TO BE RECORDED after SA-4 runs: actual `pytest -q` result, number of new cases, Ruff result, files changed, and any fix made._ |
| **Constraint** | Must not touch `services/users.py`, `services/tasks.py`, `routes/api.py`, `utils/errors.py`, `app.py` or `requirements.txt`. In `tests/test_api.py` it may only extend the import section and append the new fixture and tests; every existing fixture and test must keep its behavior. Must not touch `tests/test_tasks.py`. Must not touch `CLAUDE.md`, `PLAN_LOG.md` or `DECOMPOSITION.md`. If a new test exposes a defect in `services/users.py` or `routes/api.py`, it must stop and report, not edit those files. |
| **Hand-off** | The final `pytest -q` pass count, the number of new test cases, and a list of any contract behavior that failed or was left untested. This feeds the Divergence section. |

Prompt for SA-4:

```text
You are SA-4 (Tests) in a four-step pipeline that adds a user notification preference to this Flask task-manager project. SA-1 added the data, SA-2 the service functions and SA-3 the routes. Do only the testing step described here.

Read first: services/users.py, routes/api.py, utils/errors.py, tests/test_api.py and tests/test_tasks.py

Precondition: services/users.py must define NOTIFICATION_PREFS, DEFAULT_NOTIFICATION_PREF, list_users(), get_notification_pref() and set_notification_pref(), and routes/api.py must define GET /users, GET /users/<int:user_id>/notifications and PATCH /users/<int:user_id>/notifications. If any of these is missing, stop and tell me.

Before you edit anything: run git status --short and git diff --stat and keep the output. SA-1, SA-2 and SA-3 may have left uncommitted changes, so services/users.py and routes/api.py are expected to show as modified already. Those changes are expected. Do not modify or revert them, and do not report them as yours.

Expected behavior to test:
- Every user record has a notification_pref key. The default is None (JSON null). Valid values are None, "email", "sms" and "none". None means no preference set; "none" means notifications disabled.
- set_notification_pref(user_id, value) looks the user up first, then validates, then assigns, and returns the updated user record. None resets to the default.
- Invalid values raise ValidationError with status 422 and the message "Invalid notification_pref: must be one of email, sms, none, or null".
- An unknown user raises NotFoundError with status 404 and the message "User not found", even when the value is also invalid.
- GET /api/users returns 200 with the list of user records.
- GET /api/users/<id> returns 200 with the user record, including notification_pref.
- GET /api/users/<id>/notifications returns 200 with {"notification_pref": value}.
- PATCH /api/users/<id>/notifications with {"notification_pref": value} returns 200 with the updated user record.
- PATCH with a body that is not a JSON object returns 422 {"error": "Invalid request body: must be a JSON object"}, and this is checked before the user lookup.
- PATCH with a JSON object that has no notification_pref key returns 422 {"error": "Invalid notification_pref: is required"}.
- Error responses have the form {"error": message}.

Task part 1: create tests/test_users.py with service-level tests.
- Add a restore_users fixture that takes a copy.deepcopy snapshot of USERS, yields inside try, and in finally restores it in place with USERS.clear() and USERS.update(snapshot). Use it in every test in this file. Model it on restore_tasks in tests/test_tasks.py.
- Cover:
  a. Both seed users have notification_pref None.
  b. A record made by create_user() has notification_pref None.
  c. list_users() equals list(USERS.values()), is in id order, and clearing the returned list does not change USERS.
  d. get_notification_pref() returns None by default and returns the new value after a set.
  e. set_notification_pref() for each of "email", "sms", "none": returns the user record with the new value, stores it, and leaves the user's other fields and the other user unchanged.
  f. set_notification_pref(user_id, None) after a set resets the value to None.
  g. Invalid values, parametrized over "Email", "EMAIL", "", " email", "push", 1, 0, True, False, 2.5, [], ["email"] and {}: ValidationError, status_code 422, the exact message, and USERS equal to a deepcopy snapshot taken before the call.
  h. Unknown user 999 for get_notification_pref() and for set_notification_pref() with a valid value and with an invalid value: NotFoundError, status_code 404, message "User not found", USERS unchanged.

Task part 2: add API tests to tests/test_api.py.
- You may extend the import section of tests/test_api.py to import USERS from services.users. Append the new fixture and the new tests after the existing tests.
- Add an autouse restore_users fixture with the same snapshot and restore logic as in part 1. Keep the existing client and restore_tasks fixtures as they are.
- The two autouse fixtures must coexist: for every test in the file, restore_tasks still restores TASKS and restore_users restores USERS, and neither depends on or replaces the other.
- Cover:
  a. GET /api/users: 200, body equals list(USERS.values()), every record has a notification_pref key.
  b. GET /api/users/1: 200, body includes "notification_pref": null.
  c. GET /api/users/1/notifications: 200, body {"notification_pref": null}.
  d. PATCH for each of "email", "sms", "none": 200, body equals the original user with only notification_pref changed, and the new value then appears in GET /api/users/1/notifications, GET /api/users/1 and GET /api/users.
  e. PATCH with {"notification_pref": null} after a set: 200 and the value is null again.
  f. PATCH with invalid values, parametrized over "Email", "", "push", 1, True, [] and {}: 422, exact error body, USERS equal to a snapshot.
  g. PATCH with {} and with {"pref": "email"}: 422 with the "is required" body, USERS equal to a snapshot.
  h. PATCH with non-object bodies "[]", "\"email\"", "3" and "null", sent as data=<string> with content_type="application/json" (the test client sends no body for json=None): 422 with the "must be a JSON object" body, USERS equal to a snapshot.
  i. Unknown user 999: GET notifications is 404; PATCH with a valid value is 404; PATCH with an invalid value is 404; PATCH with a non-object body is 422. Each has the exact error body and leaves USERS equal to a snapshot.

Constraints:
- Create tests/test_users.py and add to tests/test_api.py. Change no other file.
- In tests/test_api.py, only add: an import of USERS in the import section, then the new fixture and tests. Preserve every existing fixture and test without changing its behavior; do not reorder or remove any of them.
- Do not touch tests/test_tasks.py.
- Do not touch services/users.py, services/tasks.py, routes/api.py, utils/errors.py, app.py, requirements.txt, CLAUDE.md, PLAN_LOG.md, or DECOMPOSITION.md.
- Do not weaken, skip, xfail or delete a test to make the suite pass.
- Do not commit or push.
- Other files may already show as modified or untracked from earlier pipeline steps. Do not touch or revert them.

Verification:
1. Run: .venv/Scripts/python -m pytest -q
   Expected: all 119 existing tests still pass and every new test passes. Run the complete suite, not only the new tests: this is what confirms the existing tests remain isolated with both autouse fixtures active.
2. Run: .venv/Scripts/python -m pytest -q tests/test_users.py and .venv/Scripts/python -m pytest -q tests/test_api.py -k "user or notification"
   Expected: the new tests pass on their own.
3. Run: .venv/Scripts/python -m ruff check .
   Expected: Found 5 errors. These are pre-existing findings in app.py, routes/api.py and tests/test_tasks.py. Do not fix them. Your new test code must add none; follow the import layout of tests/test_api.py.
4. Run: git status --short and git diff --stat again, and compare with the output you recorded before editing.
   Expected: the only differences are that tests/test_users.py is new and tests/test_api.py is modified. Anything that already appeared before you started belongs to SA-1, SA-2 or SA-3, not to this session.

If a new test fails because the test itself is wrong, fix the test in this session. If it fails because services/users.py or routes/api.py does not behave as described above, do not edit those files: stop and tell me the failing test, the expected and actual behavior, and the smallest fix you would propose, then wait for my instruction.

Report: the exact pytest result line, the number of new test cases per file, the exact Ruff result line, the before and after git status --short output, the files that changed during this session, and any behavior above that failed or that you could not test.
```

## Divergence

Nothing below is filled in yet. Each answer is recorded from what actually happened, after all four subagents have run.

### Did Claude follow the Constraint field for every subagent?

_TO BE RECORDED. For each of SA-1 to SA-4: constraint followed or not. For any violation or near-violation: the file path, which constraint, and what Claude did instead._

### Did any subagent's output break the next subagent's assumption?

_TO BE RECORDED. Any hand-off value that was missing, renamed or different from this document, and which precondition check caught it._

### How did you recover?

_TO BE RECORDED. The fix, the session it was made in, and the `pytest -q` result afterwards._

### Would you write the decomposition differently a second time?

_TO BE RECORDED. What would change in the boundaries, prompts or verification steps, and why._
