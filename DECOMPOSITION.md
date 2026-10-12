# PA 5, Task 2 — Subagent Pipeline: User Notification Preference

- **Finalized:** 2026-10-12, before any implementation subagent started. It was drafted with Claude Code in a preparation session that changed no implementation files.
- **Base commit:** `b089889` (PA5 Task 1 Session 4: add priority filtering)
- **Status:** All four subagents have run. Their results, the final audit and the Divergence section are recorded from the actual runs.

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
| **Result (`pytest -q`) and fixes** | **Completed** in `C:\Users\Lokes\Desktop\task-manager-pa5-fresh`. `pytest -q`: 119 passed in 0.36s. Ruff: Found 5 errors, unchanged from the baseline. Files changed: `services/users.py` only; `git diff --stat` shows 14 lines changed, 11 insertions and 3 deletions. Added `NOTIFICATION_PREFS`, `DEFAULT_NOTIFICATION_PREF`, `notification_pref` on both seed users, and the `create_user()` default. No fix was needed: the session's first test run passed and no edit followed it. No commit or push. Execution note: the SA-1 session initially started in `C:\Users\Lokes` and selected the intended repository after checking three copies; all edits were made in the intended repository. |
| **Hand-off delivered** | `NOTIFICATION_PREFS` and `DEFAULT_NOTIFICATION_PREF` are defined in `services/users.py`, ready for SA-2. |
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
| **Result (`pytest -q`) and fixes** | **Completed.** `pytest -q`: 119 passed in 0.28s; this figure is from a verification-only rerun in the same session, and the session's first run, straight after the edit, was 119 passed in 0.35s. Ruff: Found 5 errors, 4 fixable, unchanged from the baseline. Files changed: `services/users.py` only. SA-2 added `list_users()`, `get_notification_pref()` and `set_notification_pref()`; the three functions were appended without modifying existing code or adding imports. The before-and-after comparison of `git diff -- services/users.py` confirmed that all SA-1 changes were preserved. The cumulative uncommitted diff of `services/users.py` went from 11 insertions and 3 deletions after SA-1 to 57 insertions and 3 deletions after SA-2, so SA-2's share is 46 inserted lines and no deletions. Inline checks passed for valid values, the `null` reset, invalid values, unchanged state after a rejection, and `NotFoundError` precedence over `ValidationError`. `DECOMPOSITION.md` was already modified before this verification, from recording the SA-1 result, and is not an SA-2 change. No other implementation file changed. No fix was needed: the session's first test run passed and no edit followed it. No commit or push. |
| **Hand-off delivered** | `list_users()`, `get_notification_pref(user_id)` and `set_notification_pref(user_id, notification_pref)` are defined in `services/users.py`, ready for SA-3. |
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
| **Result (`pytest -q`) and fixes** | **Completed.** `pytest -q`: 119 passed in 0.26s. Ruff: Found 5 errors, all pre-existing. Files changed during SA-3: `routes/api.py` only, with 18 insertions and 1 deletion (the `services.users` import line was extended, and `list_users_route`, `get_notification_pref_route` and `update_notification_pref_route` were added after `get_user_route`). `services/users.py` and `DECOMPOSITION.md` were already modified before SA-3 and are not SA-3 changes. No file was created. No fix was needed: the session's first test run passed and no edit followed it. No commit or push. Differences between the SA-3 prompt and the implementation: none found. A post-run review outside the SA-3 session read the `routes/api.py` diff and exercised the routes in memory: all three endpoints respond; PATCH returns 422 `Invalid request body: must be a JSON object` for `[]`, a JSON string, a JSON number and `null` (also for unknown user 999, before the lookup), 422 `Invalid notification_pref: is required` for `{}`, 404 `User not found` for user 999 with a valid or an invalid value, 422 for the invalid value `"Email"`, and 200 with the updated user for `"email"`, `"sms"`, `"none"` and `null`; rejected requests left `USERS` unchanged; `GET /api/users/1` includes `notification_pref`. |
| **Hand-off delivered** | `GET /api/users`, `GET /api/users/<id>/notifications` and `PATCH /api/users/<id>/notifications` are defined in `routes/api.py` with the request and response shapes in the feature contract, ready for SA-4. |
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
| **Result (`pytest -q`) and fixes** | **Completed.** Full suite `pytest -q`: 170 passed in 0.41s, which is the 119 existing tests plus 51 new ones: 27 in `tests/test_users.py` and 24 in `tests/test_api.py`. `tests/test_users.py` alone: 27 passed. API keyword selection (`-k "user or notification"`): 25 passed, 71 deselected; the 25 are the 24 new API tests plus one existing task test whose parameter id contains `user_id`. Ruff: 5 pre-existing errors; both changed test files pass Ruff individually. Files changed during SA-4: `tests/test_users.py` (new) and `tests/test_api.py` only. In `tests/test_api.py` one import line was added in the import section and the autouse `restore_users` fixture and 12 test functions were appended; no existing line was changed or removed. Existing services and routes were unchanged. No fix was needed: the session's first test run passed and no edit followed it. No commit or push. |
| **Hand-off delivered** | Final count 170 passed with 51 new cases. No contract behavior failed. Untested cases are listed under Final audit. |
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

## Final audit

A read-only audit was run on 2026-10-12 after SA-4, outside the four subagent sessions, with all pipeline changes still uncommitted on top of `fdf93c5`.

| Check | Result |
|---|---|
| `.venv/Scripts/python -m pytest -q` | 170 passed in 0.31s |
| `.venv/Scripts/python -m pytest -q tests/test_users.py` | 27 passed |
| `.venv/Scripts/python -m pytest -q tests/test_api.py -k "user or notification"` | 25 passed, 71 deselected |
| `.venv/Scripts/python -m ruff check .` | Found 5 errors, the same five as the baseline |
| Ruff on `tests/test_users.py` and `tests/test_api.py` | All checks passed |
| `git diff --check` | No output |
| The four prompts compared with `fdf93c5` | Identical |
| Files changed against `fdf93c5` | `services/users.py`, `routes/api.py`, `tests/test_api.py`, `tests/test_users.py` (new) and this file |
| Files not changed | `services/tasks.py`, `utils/errors.py`, `app.py`, `requirements.txt`, `tests/test_tasks.py`, `CLAUDE.md`, `PLAN_LOG.md`; no `routes/users.py` was created |

The implementation matches the feature contract: the allowed values and `None` default, lookup before validation in `set_notification_pref()`, assignment only after both checks, the three routes with the body checks ahead of the service call, and `notification_pref` in the user list and detail responses. Every test in `tests/test_users.py` uses `restore_users`, and `tests/test_api.py` has autouse `restore_tasks` and `restore_users` fixtures side by side.

Session evidence, read from the four Claude Code session transcripts:

| Subagent | Session ID | Started in | Prompt body issued verbatim | User messages | Test runs in session |
|---|---|---|---|---|---|
| SA-1 | `8d9b6db8` | `C:\Users\Lokes` | Yes | 1 | 119 passed in 0.36s |
| SA-2 | `15026797` | `C:\Users\Lokes\Desktop\task-manager-pa5-fresh` | Yes | 2 | 119 passed in 0.35s, then 119 passed in 0.28s |
| SA-3 | `7f89a0ae` | `C:\Users\Lokes\Desktop\task-manager-pa5-fresh` | Yes | 1 | 119 passed in 0.26s |
| SA-4 | `5b5b0876` | `C:\Users\Lokes\Desktop\task-manager-pa5-fresh` | Yes | 1 | 170 passed in 0.41s; 27 passed; 25 passed, 71 deselected |

Each subagent ran in its own session, and the sessions ran one after another. No test run failed in any of them, and no session edited a file after its first test run, so no fix was needed anywhere in the pipeline. Each pasted prompt matched its prompt block in this file; some pastes also carried the surrounding label or code-fence markers.

Not covered by an automated test:

- An unknown user with a JSON object that has no `notification_pref` key. It was checked by hand after SA-3 and returned 422 `Invalid notification_pref: is required`.
- Malformed JSON and a missing JSON content type on the PATCH route. These were out of scope and were not checked.

## Divergence

Recorded on 2026-10-12 after all four subagents ran, from the four session reports, the four session transcripts and repository checks made between the runs.

### Did Claude follow the Constraint field for every subagent?

Yes. No file-boundary violation was found for any subagent.

| Subagent | Constraint followed | Files changed in its session |
|---|---|---|
| SA-1 | Yes | `services/users.py` only: the two constants, `notification_pref` on both seed users, and the `create_user()` default. No function was added and no signature changed. |
| SA-2 | Yes | `services/users.py` only: three functions appended, with no change to existing code and no new import. SA-1's field, defaults and constants were preserved. |
| SA-3 | Yes | `routes/api.py` only: one import line extended and three routes added. `handle_app_error` and the existing routes were not changed, and the routes do not read `USERS`. |
| SA-4 | Yes | `tests/test_users.py` (new) and `tests/test_api.py` only. No existing test or fixture was changed, and no production file was touched. |

Two things came close to a boundary without crossing it:

- **SA-1 working directory.** The SA-1 session initially started in `C:\Users\Lokes`, not in the repository. Two file searches from that directory timed out. It then found three copies of the project (`Desktop\task-manager-OLD-PA5-BACKUP\repo`, `Desktop\task-manager-pa5-fresh` and `Downloads\task-manager\task-manager`), inspected each read-only, and selected the intended repository, `C:\Users\Lokes\Desktop\task-manager-pa5-fresh`, before editing. The transcript shows edits to that repository's `services/users.py` only; the other two copies were not edited. This is not a file-boundary violation, but the prompt named files only by relative path, so it did not rule out editing a different copy.
- **SA-2 shared file.** SA-1 and SA-2 both had `services/users.py` as their Output, so `git status` could not show whether SA-2 had altered SA-1's work. SA-2 recorded `git diff -- services/users.py` before and after its edits and compared the two. The comparison showed only the three appended functions as new, and every SA-1 line still present. The uncommitted diff of that file went from 11 insertions and 3 deletions after SA-1 to 57 insertions and 3 deletions after SA-2.

`DECOMPOSITION.md` was modified between subagent runs to record results. Those edits were made in a separate documentation session, not by a subagent, so each later subagent correctly reported the file as already modified before it started.

Differences between the prewritten prompts and the implementations:

- SA-1, SA-2 and SA-3: none found.
- SA-4: nothing in the prompt's coverage list is missing. Two small additions go beyond it: the service-level reset test is parametrized over all three values where the prompt asked for one reset after a set, and the seed-user test also asserts that the user ids are 1 and 2.
- SA-4's keyword selection in verification step 2, `-k "user or notification"`, also selected one existing task test whose parameter id contains `user_id`, so it reported 25 passed, not the 24 new API tests. This is an imprecision in the prompt, not in the implementation.

One difference between the execution rules and the actual run:

- The SA-2 session received a second message after its prewritten prompt: "Finish SA-2 verification without changing any files", asking it to rerun `pytest -q`, Ruff, `git status --short` and `git diff --stat` and to confirm SA-1's changes were preserved. It was verification only. The session made no edit after that message, and the rerun gave the 119 passed in 0.28s recorded above. The other three sessions received only their prewritten prompt.

### Did any subagent's output break the next subagent's assumption?

No. Every hand-off arrived as this document specified, and no precondition check failed.

- SA-1 to SA-2: `NOTIFICATION_PREFS`, `DEFAULT_NOTIFICATION_PREF` and the `notification_pref` key were present with the specified names and values.
- SA-2 to SA-3: `list_users()`, `get_notification_pref()` and `set_notification_pref()` were present with the specified signatures, and SA-3 imported them without change.
- SA-3 to SA-4: the three routes returned the specified shapes, status codes and error messages, so all 51 new tests passed against the production code as written.

The only hand-off issue was outside the code: the SA-1 working-directory ambiguity described above, which was resolved inside the SA-1 session before any edit.

### How did you recover?

No code recovery was needed. The session transcripts show no failing test run and no fix in any subagent session, `pytest -q` was green after every subagent (119, 119, 119, then 170 passed), and no red state was carried forward.

The two process issues were handled as follows:

- **SA-1 working directory:** handled in the SA-1 session by checking the three copies and selecting the intended repository before editing. The result was then confirmed from the repository itself: `git diff --stat` there showed `services/users.py` with 11 insertions and 3 deletions.
- **SA-2 shared file:** handled before SA-2 ran, by amending its prompt to require the before-and-after `git diff -- services/users.py` comparison. SA-2 then ran with that prompt unchanged.

### Would you write the decomposition differently a second time?

Yes. The boundaries held, but the run showed five things to change:

1. **Pin the working directory in every prompt.** Each prompt should start by stating the absolute repository path and telling the session to confirm it with `git rev-parse --show-toplevel` and the expected `HEAD` before reading anything. The SA-1 session started in `C:\Users\Lokes` and had to choose between three copies.
2. **Commit after each subagent.** With one commit per subagent, each boundary would be a commit diff. That would replace the manual before-and-after comparison SA-2 needed for `services/users.py`, and the "already modified" caveats in the SA-3 and SA-4 prompts.
3. **Verify behavior earlier.** With tests last, `pytest -q` after SA-1, SA-2 and SA-3 only showed that the 119 existing tests still passed; the new behavior had no automated test until SA-4. Having each layer add its own tests, or writing the tests first, would make each `pytest -q` checkpoint prove that subagent's own work.
4. **Make the verification steps consistent and precise.** SA-1's prompt checks `git status` only afterwards, while the execution rules call for before and after. SA-4's `-k "user or notification"` selector should name the new tests exactly, because it also matched an existing task test.
5. **Close the known test gap in the SA-4 prompt.** Add the case of an unknown user with a JSON object that has no `notification_pref` key, which is the one contract behavior left without an automated test.
