# Decomposition

COMP 4600/5300 PA 5, Task 2: user notification preference, split across three subagents.

This document was written before any subagent ran. The prompts in it are used verbatim.

It was drafted with Claude Code, in the same session as Task 1 Plan Mode Session 4, and reviewed
before any subagent ran. The assignment asks for it to be written before opening Claude Code; that
was not done and cannot be changed afterwards. See "Divergence".

## Starting checkpoint

- Commit: `48813e4` (`PA 5 Task 1: GET priority filtering and Plan Mode session 4`)
- Working tree: clean
- `.venv/Scripts/python -m pytest -q`: 127 passed
- `.venv/Scripts/python -m ruff check .`: 5 findings (`app.py` I001, `routes/api.py` I001 and
  F401, `tests/test_tasks.py` I001 and B017)

`CLAUDE.md` still states an older baseline (4 tests, 6 Ruff findings). It is not edited in Task 2;
each prompt below states the real baseline instead.

## Feature

Add a per-user notification preference with allowed values `email`, `sms`, `none`; default `none`.

1. Store `notification_pref` for every user in the existing in-memory `USERS` dictionary.
2. Include `notification_pref` in user list and detail responses.
3. `PATCH /api/users/<id>/notifications` updates the preference.
4. `GET /api/users/<id>/notifications` returns the preference.
5. Invalid values raise the existing `ValidationError` (422).
6. Unknown users raise the existing `NotFoundError` (404).
7. Existing behaviour and all 127 existing tests stay intact.

Source of requirements: the Task 2 instructions supplied in the planning session. No Task 2
requirements file exists in this repository.

## Discrepancies between the assignment and this repository

| Assignment assumes | Repository has | Decision |
|---|---|---|
| A nullable database column and a migration | Module-level dictionaries (`USERS`, `TASKS`); `CLAUDE.md` forbids moving them | No database, no migration. `notification_pref` is a key on every user record. "Not set" is the string `"none"`, never Python `None` or JSON `null`. |
| An existing user list response | No `list_users` service and no `GET /api/users` route; only `GET /api/users/<id>` | Subagent A adds `list_users()`; Subagent B adds `GET /api/users` returning a bare JSON array. Decided during planning, before execution. |
| An existing user detail response | `GET /api/users/<id>` returns the stored record via `get_user` | No route change needed; the field appears once A adds it to the records. |

## Agreed contract

Fixed here so all three subagents work to the same definition.

### Service layer (`services/users.py`)

| Name | Signature | Behaviour |
|---|---|---|
| `NOTIFICATION_PREFS` | `("email", "sms", "none")` | Allowed values |
| `DEFAULT_NOTIFICATION_PREF` | `"none"` | Default |
| `USERS` seed records | unchanged ids, names, emails | each gains `"notification_pref": "none"` |
| `get_user` | unchanged | unchanged |
| `create_user` | unchanged signature `(name: str, email: str) -> dict` | new record includes `"notification_pref": "none"` |
| `list_users` | `() -> list[dict]` | new list of every user record, in `USERS` insertion order |
| `get_notification_pref` | `(user_id: int) -> str` | returns the stored value; `NotFoundError("User")` if unknown |
| `update_notification_pref` | `(user_id: int, updates: object) -> dict` | validates, stores, returns the updated user record |

`update_notification_pref` checks, in this order (the same order as `update_task_priority` in
`services/tasks.py`):

| Condition | Error | Message |
|---|---|---|
| unknown `user_id` | `NotFoundError` 404 | `User not found` |
| `updates` is not a `dict` | `ValidationError` 422 | `Invalid request: must be a JSON object` |
| any key other than `notification_pref` | `ValidationError` 422 | `Invalid request: only notification_pref can be updated` |
| `notification_pref` key missing | `ValidationError` 422 | `Invalid notification_pref: is required` |
| value is not exactly the `str` `"email"`, `"sms"` or `"none"` | `ValidationError` 422 | `Invalid notification_pref: must be one of: email, sms, none` |

Values are matched exactly. `None`, `"EMAIL"`, `" email"`, `""`, `"push"`, numbers, booleans, lists
and dicts are all rejected, and a rejected call leaves `USERS` unchanged.

### HTTP layer (`routes/api.py`)

| Method and path | Success | Errors |
|---|---|---|
| `GET /api/users` | 200, bare JSON array of user records | none |
| `GET /api/users/<int:user_id>` (existing, not edited) | 200, user record now including `notification_pref` | 404 |
| `GET /api/users/<int:user_id>/notifications` | 200, `{"notification_pref": "<value>"}` | 404 `{"error": "User not found"}` |
| `PATCH /api/users/<int:user_id>/notifications` with JSON body `{"notification_pref": "<value>"}` | 200, `{"notification_pref": "<value>"}` | 404; 422 `{"error": "<message above>"}` |

Errors reach the client through the existing `@api.errorhandler(AppError)`; it is not edited.

## Execution order and handoffs

**A → B → C.** Each subagent runs in a fresh Claude Code session (`/clear` or relaunch) and
receives only its prompt from this document, verbatim.

```
A (services/users.py) --handoffs/subagent-a-service.md--> B (routes/api.py)
B                     --handoffs/subagent-b-api.md------> C (tests/test_notifications.py)
A                     --handoffs/subagent-a-service.md--> C
C                     --handoffs/subagent-c-tests.md----> reviewer
```

After each subagent: run `.venv/Scripts/python -m pytest -q`. A failure is resolved inside that
same subagent session before the next one starts, within that subagent's file boundary.

### File boundaries

| File | A | B | C |
|---|---|---|---|
| `services/users.py` | **write** | read | read |
| `routes/api.py` | no access needed | **write** | read |
| `tests/test_notifications.py` (new) | none | none | **write** |
| `handoffs/subagent-a-service.md` (new) | **write** | read | read |
| `handoffs/subagent-b-api.md` (new) | none | **write** | read |
| `handoffs/subagent-c-tests.md` (new) | none | none | **write** |
| `tests/test_tasks.py` | read | read | read |
| `services/tasks.py`, `app.py`, `utils/errors.py`, `CLAUDE.md`, `DECOMPOSITION.md` | read | read | read |
| `requirements.txt`, `PLAN_LOG.md`, `plans/`, Week 4 documents | none | none | none |

No subagent commits or pushes.

### Boundary corrections made during planning

The proposed boundaries gave each subagent one code file only. Two adjustments were needed:

1. **Handoff files.** Fresh sessions share no memory and the prompts are fixed in advance, so
   each subagent also writes exactly one handoff file under `handoffs/`.
2. **Failures C cannot fix.** C may not edit implementation files. If a new test fails because
   of a defect in `services/users.py` or `routes/api.py`, C keeps the correct test, records the
   failure in its handoff, and stops. The owning subagent is rerun in a fresh session and the
   event is logged under Divergence. C fixes in-session only failures caused by its own file.

Because C owns all new tests, pytest after A and after B proves only that the 127 existing tests
still pass. A and B therefore also run a smoke check with `python -c`, which writes no file.

---

## Subagent A: user service

- **Responsibility:** notification preference storage, defaults, validation, retrieval, update
  and user listing in the service layer.
- **May read:** `CLAUDE.md`, `DECOMPOSITION.md`, `services/users.py`, `services/tasks.py`,
  `utils/errors.py`, `tests/test_tasks.py`.
- **Deliverable:** `services/users.py` implementing the service-layer contract above.
- **May modify:** `services/users.py`, `handoffs/subagent-a-service.md`.
- **Must not modify:** `routes/api.py`, `services/tasks.py`, `tests/` (any file), `app.py`,
  `utils/errors.py`, `requirements.txt`, `CLAUDE.md`, `DECOMPOSITION.md`, `PLAN_LOG.md`, `plans/`,
  any other file.
- **Handoff artifact:** `handoffs/subagent-a-service.md` with function signatures, validation
  behaviour, error messages and verification results.
- **Verification:** `.venv/Scripts/python -m pytest -q` (expect 127 passed). Any failure is fixed
  in this session before handoff.

### Prompt A

````text
You are Subagent A (user service) for COMP 4600/5300 PA 5 Task 2 in the task-manager repository.
This is a fresh session. Work only from this prompt and the files named in it.

READ FIRST
- CLAUDE.md (project conventions; note its baseline numbers are stale)
- DECOMPOSITION.md, sections "Agreed contract" and "Subagent A"
- services/users.py
- services/tasks.py (reference only: see _validate_priority and update_task_priority for the
  validation style and check order to mirror)
- utils/errors.py
- tests/test_tasks.py (reference only)

ACTUAL BASELINE
- .venv/Scripts/python -m pytest -q -> 127 passed
- .venv/Scripts/python -m ruff check . -> 5 findings, none in services/users.py

FILES YOU MAY MODIFY
- services/users.py
- handoffs/subagent-a-service.md (create it)

FILES YOU MUST NOT MODIFY
routes/api.py, services/tasks.py, anything under tests/, app.py, utils/errors.py,
requirements.txt, CLAUDE.md, DECOMPOSITION.md, PLAN_LOG.md, plans/, and every other file.
Do not create test files. Do not commit or push.

GOAL
Add a per-user notification preference to the service layer. Allowed values are exactly the
strings "email", "sms" and "none". The default is "none". The project stores data in the
module-level USERS dictionary; do not introduce a database, a migration, or a new dependency,
and do not move USERS.

IMPLEMENT IN services/users.py
1. Module constants:
   NOTIFICATION_PREFS = ("email", "sms", "none")
   DEFAULT_NOTIFICATION_PREF = "none"
2. Add "notification_pref": "none" to both seeded USERS records. Do not change their ids,
   names or emails.
3. create_user: keep the signature (name: str, email: str) -> dict and all existing validation.
   The new record must include "notification_pref" set to the default.
4. get_user: do not change it.
5. A private helper _validate_notification_pref(value: object) -> str that returns the value if
   it is exactly one of the allowed strings and otherwise raises
   ValidationError("notification_pref", "must be one of: email, sms, none").
   Check the type first (type(value) is not str) so unhashable values such as lists and dicts
   raise ValidationError, not TypeError. Do not strip, lowercase, or otherwise coerce.
6. list_users() -> list[dict]: return a new list of every user record in USERS insertion order.
7. get_notification_pref(user_id: int) -> str: return the stored preference. Unknown users raise
   NotFoundError("User"); reuse get_user for the lookup.
8. update_notification_pref(user_id: int, updates: object) -> dict: perform these checks in this
   exact order, then store the value and return the updated user record:
   a. unknown user -> NotFoundError("User") (reuse get_user)
   b. type(updates) is not dict -> ValidationError("request", "must be a JSON object")
   c. any key other than "notification_pref" ->
      ValidationError("request", "only notification_pref can be updated")
   d. "notification_pref" missing -> ValidationError("notification_pref", "is required")
   e. invalid value -> the error from _validate_notification_pref
   A rejected call must leave USERS completely unchanged.

CONVENTIONS
- Type hints on every parameter and return value.
- Google-style docstrings with Args, Returns and Raises sections where applicable, matching the
  existing functions in services/users.py.
- Use NotFoundError and ValidationError from utils/errors.py. No raw KeyError or Exception.
- Match the existing code style in the file. Do no unrelated cleanup.

VERIFY BEFORE HANDOFF
1. .venv/Scripts/python -m pytest -q
   Expect 127 passed. If anything fails, fix it in this session, inside services/users.py only,
   and rerun until it passes. Never edit a test to make it pass.
2. .venv/Scripts/python -m ruff check .
   Expect the same 5 findings and none in services/users.py.
3. Smoke check (writes no file):
   .venv/Scripts/python -c "from services.users import list_users, get_notification_pref, update_notification_pref; print(list_users()); print(get_notification_pref(1)); print(update_notification_pref(1, {'notification_pref': 'sms'})); print(get_notification_pref(1))"
   Also confirm by a similar one-off command that an invalid value and an unknown user raise
   the expected errors.
4. git status --short
   Expect only services/users.py modified and handoffs/subagent-a-service.md untracked.

HANDOFF
Write handoffs/subagent-a-service.md containing:
- Every public name added or changed, with its exact signature and return value.
- The validation rules, the order of checks, and the exact error message for each case.
- The actual output of the four verification steps (test count, Ruff count, smoke output,
  git status).
- Anything that differs from DECOMPOSITION.md "Agreed contract", stated plainly, or the sentence
  "No difference from the agreed contract." Report only what actually happened.

If the contract cannot be implemented as written, stop and explain why in the handoff file
instead of inventing different behaviour. Finish by summarising what you changed.
````

---

## Subagent B: API integration

- **Responsibility:** expose the user service functions over HTTP.
- **May read:** `CLAUDE.md`, `DECOMPOSITION.md`, `handoffs/subagent-a-service.md`,
  `services/users.py`, `routes/api.py`, `app.py`, `utils/errors.py`, `tests/test_tasks.py`.
- **Deliverable:** `routes/api.py` with `GET /api/users`,
  `GET /api/users/<id>/notifications` and `PATCH /api/users/<id>/notifications`.
- **May modify:** `routes/api.py`, `handoffs/subagent-b-api.md`.
- **Must not modify:** `services/users.py`, `services/tasks.py`, `tests/` (any file), `app.py`,
  `utils/errors.py`, `requirements.txt`, `CLAUDE.md`, `DECOMPOSITION.md`, `PLAN_LOG.md`, `plans/`,
  `handoffs/subagent-a-service.md`, any other file.
- **Handoff artifact:** `handoffs/subagent-b-api.md` with endpoint contracts, HTTP status
  behaviour and verification results.
- **Depends on:** Subagent A complete, `handoffs/subagent-a-service.md` present.
- **Verification:** `.venv/Scripts/python -m pytest -q` (expect 127 passed). Any failure is fixed
  in this session before handoff.

### Prompt B

````text
You are Subagent B (API integration) for COMP 4600/5300 PA 5 Task 2 in the task-manager
repository. This is a fresh session. Work only from this prompt and the files named in it.
Subagent A has already finished the service layer.

READ FIRST
- CLAUDE.md (project conventions; note its baseline numbers are stale)
- DECOMPOSITION.md, sections "Agreed contract" and "Subagent B"
- handoffs/subagent-a-service.md (Subagent A's handoff: the functions you will call)
- services/users.py (read only)
- routes/api.py
- app.py and utils/errors.py (read only)
- tests/test_tasks.py (reference only)

If handoffs/subagent-a-service.md is missing, or the functions it describes are not in
services/users.py, stop and report that. Do not implement service logic yourself.

ACTUAL BASELINE
- .venv/Scripts/python -m pytest -q -> 127 passed
- .venv/Scripts/python -m ruff check . -> 5 findings; two are in routes/api.py (I001 on the
  import block and F401 on the unused process_order import). Leave both exactly as they are.

FILES YOU MAY MODIFY
- routes/api.py
- handoffs/subagent-b-api.md (create it)

FILES YOU MUST NOT MODIFY
services/users.py, services/tasks.py, anything under tests/, app.py, utils/errors.py,
requirements.txt, CLAUDE.md, DECOMPOSITION.md, PLAN_LOG.md, plans/,
handoffs/subagent-a-service.md, and every other file.
Do not create test files. Do not commit or push.

GOAL
Add three routes to the existing "api" blueprint in routes/api.py. The blueprint is mounted at
/api in app.py.

1. GET /users
   Return 200 with jsonify(list_users()): a bare JSON array of user records.
2. GET /users/<int:user_id>/notifications
   Return 200 with {"notification_pref": <value from get_notification_pref(user_id)>}.
3. PATCH /users/<int:user_id>/notifications
   Pass user_id and request.get_json() straight to update_notification_pref, and return 200 with
   {"notification_pref": <the updated record's notification_pref>}.

RULES
- Routes handle HTTP concerns only. Do not validate the preference, check the body shape, or
  look up users in the route; the service does all of that and raises AppError subclasses.
- Do not change @api.errorhandler(AppError). It already converts NotFoundError to 404 and
  ValidationError to 422 with a body of {"error": "<message>"}.
- Do not change any existing route, including GET /users/<int:user_id>, the task routes, and
  their behaviour. The user detail response gains notification_pref automatically because the
  service record now contains it.
- Add the new service names to the existing "from services.users import get_user" line. Do not
  reorder or tidy the import block and do not remove the unused process_order import.
- Match the existing style of the file. Do no unrelated cleanup.

EXPECTED HTTP BEHAVIOUR
- GET /api/users -> 200, array with one object per user, each including notification_pref
- GET /api/users/1 -> 200, object including notification_pref
- GET /api/users/1/notifications -> 200 {"notification_pref": "none"} on seeded data
- GET /api/users/999/notifications -> 404 {"error": "User not found"}
- PATCH /api/users/1/notifications {"notification_pref": "email"} -> 200
  {"notification_pref": "email"}
- PATCH with an invalid value -> 422
  {"error": "Invalid notification_pref: must be one of: email, sms, none"}
- PATCH with {} -> 422 {"error": "Invalid notification_pref: is required"}
- PATCH with an extra field -> 422
  {"error": "Invalid request: only notification_pref can be updated"}
- PATCH with a JSON array or JSON null body -> 422
  {"error": "Invalid request: must be a JSON object"}
- PATCH /api/users/999/notifications -> 404 {"error": "User not found"}

VERIFY BEFORE HANDOFF
1. .venv/Scripts/python -m pytest -q
   Expect 127 passed. If anything fails, fix it in this session, inside routes/api.py only, and
   rerun until it passes. Never edit a test to make it pass.
2. .venv/Scripts/python -m ruff check .
   Expect the same 5 findings and no new one.
3. Smoke check (writes no file):
   .venv/Scripts/python -c "from app import app; c = app.test_client(); print(c.get('/api/users').get_json()); print(c.get('/api/users/1').get_json()); print(c.get('/api/users/1/notifications').get_json()); r = c.patch('/api/users/1/notifications', json={'notification_pref': 'email'}); print(r.status_code, r.get_json()); r = c.patch('/api/users/1/notifications', json={'notification_pref': 'fax'}); print(r.status_code, r.get_json()); r = c.get('/api/users/999/notifications'); print(r.status_code, r.get_json())"
4. git status --short
   Expect routes/api.py modified and handoffs/subagent-b-api.md untracked, in addition to
   Subagent A's services/users.py and handoffs/subagent-a-service.md.

If a smoke check shows a wrong result that comes from services/users.py, do not edit that file.
Record the problem in your handoff and stop.

HANDOFF
Write handoffs/subagent-b-api.md containing:
- Each new route: method, full path, request body, success status and body, error statuses and
  bodies.
- Confirmation of which existing routes were left untouched.
- The actual output of the four verification steps.
- Anything that differs from DECOMPOSITION.md "Agreed contract", stated plainly, or the sentence
  "No difference from the agreed contract." Report only what actually happened.

Finish by summarising what you changed.
````

---

## Subagent C: tests

- **Responsibility:** service-level and Flask API-level tests for the notification preference.
- **May read:** `CLAUDE.md`, `DECOMPOSITION.md`, `handoffs/subagent-a-service.md`,
  `handoffs/subagent-b-api.md`, `services/users.py`, `routes/api.py`, `app.py`,
  `utils/errors.py`, `tests/test_tasks.py`.
- **Deliverable:** new file `tests/test_notifications.py`.
- **May modify:** `tests/test_notifications.py`, `handoffs/subagent-c-tests.md`.
- **Must not modify:** `tests/test_tasks.py`, `services/users.py`, `services/tasks.py`,
  `routes/api.py`, `app.py`, `utils/errors.py`, `requirements.txt`, `CLAUDE.md`,
  `DECOMPOSITION.md`, `PLAN_LOG.md`, `plans/`, the other two handoff files, any other file.
- **Handoff artifact:** `handoffs/subagent-c-tests.md` with test results and a coverage summary.
- **Depends on:** Subagents A and B complete, both handoff files present.
- **Verification:** `.venv/Scripts/python -m pytest -q` (expect 127 existing plus all new tests
  passing). Failures caused by the test file are fixed in this session before handoff; failures
  caused by an implementation defect are reported, not worked around.

### Prompt C

````text
You are Subagent C (tests) for COMP 4600/5300 PA 5 Task 2 in the task-manager repository.
This is a fresh session. Work only from this prompt and the files named in it.
Subagent A has finished the service layer and Subagent B has finished the routes.

READ FIRST
- CLAUDE.md (project conventions; note its baseline numbers are stale)
- DECOMPOSITION.md, sections "Agreed contract" and "Subagent C"
- handoffs/subagent-a-service.md and handoffs/subagent-b-api.md
- services/users.py and routes/api.py (read only)
- app.py and utils/errors.py (read only)
- tests/test_tasks.py (read only: follow its style, its restore_tasks fixture pattern, and its
  client fixture)

If either handoff file is missing, stop and report that.

ACTUAL BASELINE
- .venv/Scripts/python -m pytest -q -> 127 passed, all in tests/test_tasks.py
- .venv/Scripts/python -m ruff check . -> 5 findings

FILES YOU MAY MODIFY
- tests/test_notifications.py (create it)
- handoffs/subagent-c-tests.md (create it)

FILES YOU MUST NOT MODIFY
tests/test_tasks.py, services/users.py, services/tasks.py, routes/api.py, app.py,
utils/errors.py, requirements.txt, CLAUDE.md, DECOMPOSITION.md, PLAN_LOG.md, plans/,
handoffs/subagent-a-service.md, handoffs/subagent-b-api.md, and every other file.
Do not create conftest.py. Do not commit or push.

GOAL
Write tests/test_notifications.py covering the notification preference at the service level and
through the Flask API. Test against the "Agreed contract" in DECOMPOSITION.md. Where a handoff
file disagrees with that contract, the contract is the expectation; note the disagreement in
your handoff.

FIXTURES (define them inside tests/test_notifications.py)
- restore_users: deep-copy USERS before the test and, in a finally block, clear USERS and
  restore the snapshot. Same pattern as restore_tasks in tests/test_tasks.py.
- client: app.test_client().
USERS is module-level state shared by every test. Every test in this file must request
restore_users, including read-only tests.

REQUIRED COVERAGE
Service level:
- Both seeded users have notification_pref "none".
- create_user returns and stores a record with notification_pref "none".
- list_users returns every user record, each with notification_pref, as a new list (clearing
  the returned list does not change USERS).
- get_user returns a record that includes notification_pref.
- get_notification_pref returns the stored value, and NotFoundError (404, "User not found") for
  an unknown user.
- update_notification_pref with each of "email", "sms", "none": returns the updated user
  record, stores the value, and leaves other users unchanged.
- update_notification_pref with invalid values, parametrized over at least: None, "", "push",
  "EMAIL", " email", "email ", 1, True, ["email"], {"a": 1}. Each raises ValidationError with
  status 422 and message "Invalid notification_pref: must be one of: email, sms, none", and
  USERS equals a deep copy taken beforehand.
- update_notification_pref with invalid updates: {} ("Invalid notification_pref: is required"),
  an unknown key and a valid key plus an extra key
  ("Invalid request: only notification_pref can be updated"), [] and None
  ("Invalid request: must be a JSON object"). USERS unchanged each time.
- update_notification_pref for an unknown user raises NotFoundError even when the body is also
  invalid, and USERS is unchanged.

API level (through client):
- GET /api/users -> 200, body equals the list of stored records, each with notification_pref.
- GET /api/users/1 -> 200, body includes notification_pref.
- GET /api/users/1/notifications -> 200 {"notification_pref": "none"}.
- GET /api/users/999/notifications -> 404 {"error": "User not found"}.
- PATCH /api/users/1/notifications with each valid value -> 200 {"notification_pref": value},
  and a following GET of /notifications, /api/users/1 and /api/users reflects the change.
- PATCH with invalid values (JSON-representable ones from the list above) -> 422 with the exact
  error body, USERS unchanged.
- PATCH with {}, with an extra field, with a JSON array, and with a literal JSON null body
  (data="null", content_type="application/json") -> 422 with the matching message, USERS
  unchanged.
- PATCH /api/users/999/notifications -> 404 {"error": "User not found"}, USERS unchanged.

Do not test behaviour the contract does not define (for example non-JSON content types or
malformed JSON).

CONVENTIONS
- Plain pytest functions and pytest.mark.parametrize, in the style of tests/test_tasks.py.
- The new file must have zero Ruff findings. Keep imports sorted so it does not add an I001
  finding, and do not use pytest.raises(Exception).

VERIFY BEFORE HANDOFF
1. .venv/Scripts/python -m pytest -q
   All 127 existing tests and every new test must pass.
2. .venv/Scripts/python -m ruff check .
   Expect the same 5 findings and none in tests/test_notifications.py.
3. git status --short
   Expect tests/test_notifications.py and handoffs/subagent-c-tests.md untracked, in addition
   to the changes left by Subagents A and B, and nothing else.

HANDLING FAILURES
- If a new test fails because the test itself is wrong (bad fixture, typo, wrong expectation
  relative to the contract), fix the test in this session and rerun until it passes.
- If a new test fails because services/users.py or routes/api.py does not meet the contract,
  do NOT edit those files, and do NOT weaken, skip, xfail or delete the test to get a green
  run. Keep the correct test, record the failing test name, the expected and actual result,
  and which file is at fault in your handoff, then stop.
- If one of the 127 existing tests fails, do not edit tests/test_tasks.py. Report it the same
  way.

HANDOFF
Write handoffs/subagent-c-tests.md containing:
- The actual pytest summary line and the number of new test cases, split into service level
  and API level.
- A coverage summary: one line per test function saying which behaviour it covers.
- The actual Ruff and git status output.
- Any implementation defect found, any disagreement between the handoff files and the contract,
  and any required behaviour you could not cover, or the sentence "No defects or gaps found."
  Report only what actually happened.

Finish by summarising what you added.
````

---

## Subagent table

Reconstructed after execution to present each subagent in the assignment's six fields. Every field
except the pytest result restates the "Subagent A/B/C" sections and prompts above, which are
unchanged. The pytest lines are the actual results from each subagent's session transcript.

| Field | SA-A: User service | SA-B: API integration | SA-C: Tests |
|---|---|---|---|
| Subagent # | SA-A: User service | SA-B: API integration | SA-C: Tests |
| Input | `CLAUDE.md`, `DECOMPOSITION.md`, `services/users.py`, `services/tasks.py`, `utils/errors.py`, `tests/test_tasks.py` | `CLAUDE.md`, `DECOMPOSITION.md`, `handoffs/subagent-a-service.md`, `services/users.py`, `routes/api.py`, `app.py`, `utils/errors.py`, `tests/test_tasks.py` | `CLAUDE.md`, `DECOMPOSITION.md`, `handoffs/subagent-a-service.md`, `handoffs/subagent-b-api.md`, `services/users.py`, `routes/api.py`, `app.py`, `utils/errors.py`, `tests/test_tasks.py` |
| Task | Adds notification preference storage, default, validation, retrieval, update and user listing to the service layer. | Exposes the user service functions over HTTP as three routes. | Writes service-level and API-level tests for the notification preference against the agreed contract. |
| Output | Modifies `services/users.py`; creates `handoffs/subagent-a-service.md`. `pytest -q`: `127 passed in 0.28s`. | Modifies `routes/api.py`; creates `handoffs/subagent-b-api.md`. `pytest -q`: `127 passed in 0.24s`. | Creates `tests/test_notifications.py` and `handoffs/subagent-c-tests.md`. `pytest -q`: `183 passed in 0.30s` (127 existing, 56 new). |
| Constraint | Must not touch `routes/api.py`, `services/tasks.py`, anything under `tests/`, `app.py`, `utils/errors.py`, `requirements.txt`, `CLAUDE.md`, `DECOMPOSITION.md`, `PLAN_LOG.md`, `plans/`, or any other file. | Must not touch `services/users.py`, `services/tasks.py`, anything under `tests/`, `app.py`, `utils/errors.py`, `requirements.txt`, `CLAUDE.md`, `DECOMPOSITION.md`, `PLAN_LOG.md`, `plans/`, `handoffs/subagent-a-service.md`, or any other file. | Must not touch `tests/test_tasks.py`, `services/users.py`, `services/tasks.py`, `routes/api.py`, `app.py`, `utils/errors.py`, `requirements.txt`, `CLAUDE.md`, `DECOMPOSITION.md`, `PLAN_LOG.md`, `plans/`, `handoffs/subagent-a-service.md`, `handoffs/subagent-b-api.md`, or any other file. |
| Hand-off | `handoffs/subagent-a-service.md`: function signatures, validation order, exact error messages, verification output. Needed by B and C. | `handoffs/subagent-b-api.md`: each route's method, path, bodies and status codes, verification output. Needed by C. | `handoffs/subagent-c-tests.md`: pytest summary, per-test coverage, defects or gaps found. Needed by the reviewer. |

No test failed in any subagent session, so no fix was needed and none is recorded.

## Verification after all three subagents

1. `.venv/Scripts/python -m pytest -q`: 127 existing tests plus the new tests, all passing.
2. `.venv/Scripts/python -m ruff check .`: the same 5 findings, none new.
3. `git diff --check`: no output.
4. `git status --short`: `services/users.py` and `routes/api.py` modified;
   `tests/test_notifications.py`, `handoffs/` and this document new; nothing else.
5. `git diff -- tests/test_tasks.py services/tasks.py app.py utils/errors.py`: empty.

## Divergence

Completed after all three subagents ran. Final verification was run on 2026-10-11 against commit
`48813e4` plus the uncommitted Task 2 changes.

### How this section was checked

Two kinds of statement appear below and they are kept apart:

- **Verified**: observed directly during final verification, by running a command or reading the
  file.
- **Reported**: stated in a handoff file and not independently reproducible afterwards.

Final verification was run in the same Claude Code session that had just acted as Subagent C, not
in a fresh session. The checks themselves are command output and do not depend on that, but the
session had no view of the Subagent A or Subagent B sessions.

### Final verification output

| Check | Result | Status |
|---|---|---|
| `.venv/Scripts/python -m pytest -q` | `183 passed in 0.27s` | Verified |
| `pytest -q tests/test_tasks.py` | `127 passed` | Verified |
| `pytest -q tests/test_notifications.py` | `56 passed` (31 service, 25 API) | Verified |
| `.venv/Scripts/python -m ruff check .` | 5 findings, identical to the starting checkpoint: `app.py` I001, `routes/api.py` I001 and F401, `tests/test_tasks.py` I001 and B017. None in `services/users.py` or `tests/test_notifications.py` | Verified |
| `git diff --check` | no output, exit 0 | Verified |
| `git status --short` | ` M routes/api.py`, ` M services/users.py`, `?? DECOMPOSITION.md`, `?? handoffs/`, `?? tests/test_notifications.py` | Verified |
| `git diff -- tests/test_tasks.py services/tasks.py app.py utils/errors.py` | empty | Verified |
| `requirements.txt`, `CLAUDE.md`, `PLAN_LOG.md`, `plans/` | not listed by `git status`, so unmodified | Verified |
| `handoffs/` contents | `subagent-a-service.md`, `subagent-b-api.md`, `subagent-c-tests.md`, nothing else | Verified |
| HEAD | still `48813e4`; nothing committed | Verified |

`git diff --check` only inspects tracked files. The untracked `tests/test_notifications.py` and
the three handoff files were checked separately for trailing whitespace; none was found.

The implementation was also read against the "Agreed contract":

- `services/users.py`: constants, seed records, `create_user`, `list_users`,
  `get_notification_pref` and `update_notification_pref` match the contract, including the order
  of checks. The only removed lines in the diff are the two seed records, one docstring line and
  the `create_user` record literal; `get_user` is untouched.
- `routes/api.py`: the diff is 14 insertions and 1 deletion: the extended `services.users` import
  line and three new routes appended at the end. The error handler and every existing route are
  untouched.

### Per-subagent results

| Subagent | Prompt used verbatim | Stayed in boundary | pytest result | Divergence observed |
|---|---|---|---|---|
| A | Yes. The first message of the A session transcript is byte-identical to "Prompt A" (4,992 characters). | Yes for writes. The transcript shows A wrote only `services/users.py` (through a shell heredoc, not the Edit tool) and `handoffs/subagent-a-service.md`. | Verified in the A transcript: `127 passed in 0.28s`. | No constraint violated, and no difference from the agreed contract. Input not followed exactly: A read the whole of `DECOMPOSITION.md`, not only the two named sections, and did not open `tests/test_tasks.py`. |
| B | Yes. The first message of the B session transcript is byte-identical to "Prompt B" (5,306 characters). | Yes for writes. The transcript shows B edited only `routes/api.py` and created `handoffs/subagent-b-api.md`. | Verified in the B transcript: `127 passed in 0.24s`. | No constraint violated, and no difference from the agreed contract. Input not followed exactly: B read the whole of `DECOMPOSITION.md` and did not open `tests/test_tasks.py`. |
| C | Yes. The first message of the C session transcript is byte-identical to "Prompt C" (6,233 characters). | Yes. C created `tests/test_notifications.py` and `handoffs/subagent-c-tests.md` and wrote to no other file. | Verified: `183 passed` (127 existing + 56 new). All 56 new cases passed on the first run; no test was weakened, skipped or changed to get a green run. | No constraint violated. Input not followed exactly: C read the whole of `DECOMPOSITION.md`. C's handoff records "No defects or gaps found." |

What Git can and cannot show about boundaries: the set of changed files is exactly the union of
the three allowed sets, and no forbidden file changed. Git cannot attribute an edit to a
particular session, and because `DECOMPOSITION.md` and `handoffs/` are untracked there is no
history to prove that no subagent edited this document or another subagent's handoff. That rests
on the handoff reports.

### Small differences from what the prompts predicted

These are not contract deviations and needed no fix. They are recorded because they happened.

1. **`git status` expectations.** Prompts A, B and C each listed the entries they expected from
   `git status --short`. The real output also shows `?? DECOMPOSITION.md` (this document was
   untracked from the start) and shows the handoffs as the single entry `?? handoffs/` rather
   than one line per file. A, B and C each noted this in their handoff.
2. **Ruff output format.** B and C ran Ruff with `--output-format concise` added so the findings
   fit on one line each. The findings are the same 5.
3. **Starting checkpoint wording.** This document says "Working tree: clean" at the starting
   checkpoint, while `DECOMPOSITION.md` itself was an untracked file at that point. Tracked files
   were clean.

### Divergence questions

**Were boundaries respected?**
Yes, as far as it can be checked. The changed files are exactly `services/users.py` (A),
`routes/api.py` (B), `tests/test_notifications.py` (C) and one handoff file each. The protected
files `tests/test_tasks.py`, `services/tasks.py`, `app.py`, `utils/errors.py`, `requirements.txt`,
`CLAUDE.md`, `PLAN_LOG.md` and `plans/` have no changes, and nothing was committed. C's boundary
was observed directly; A's and B's are supported by the diff and by their own reports.

**Did handoffs cause problems, and how were they resolved?**
No. Both upstream handoffs were present when the next subagent started, both matched the agreed
contract, and neither disagreed with the code. B did not have to stop for a missing service
function and C did not find a defect, so the "failures C cannot fix" path planned above was never
used and no subagent was rerun. Nothing needed resolving.

One reason the handoffs carried little risk is that the contract was fixed in this document
before any subagent ran. B and C could have worked from the contract alone; the handoffs mainly
confirmed that it had been implemented as written.

**What would you improve next time?**

1. Commit `DECOMPOSITION.md` before the first subagent runs, and commit after each subagent (or
   at least record `git status` and a diff stat). Then each boundary can be proved from history
   instead of from the subagent's own report, and the `git status` expectations in the prompts
   would have been exact.
2. Have each subagent record in its handoff a checksum or copy of the prompt it received, so
   "prompt used verbatim" can be verified afterwards for all three, not only for the last one.
3. Run final verification in a fresh session rather than in the session that acted as Subagent C,
   so the reviewer is independent of every author.
4. Give A and B a real test to run. Because C owned all tests, pytest after A and after B only
   proved that the existing 127 tests still passed, and their new behaviour was covered only by
   one-off `python -c` smoke checks until C ran. Running the test subagent first, against the
   contract, would have given A and B failing tests to turn green.
5. State the expected `git status` output in the prompts from an actual run, including
   pre-existing untracked files, so a subagent does not have to explain a mismatch.

### Corrections after reading the subagent transcripts

Added on 2026-10-11. This section was first written without the Subagent A and B transcripts and
said that their prompts and pytest runs could not be checked afterwards. That was wrong: the three
session transcripts exist locally. The "Per-subagent results" table above now reflects them; the
rest of this section is left as first written, so statements elsewhere in it that describe A and B
as only "reported" are superseded by that table.

Answers to the assignment's three questions, on the transcript evidence:

- Did Claude follow the constraint field for every subagent? Yes. No subagent modified a file its
  constraint named. The Input field was not followed exactly: all three read the whole of this
  document instead of the two sections their prompt named, and A and B did not open
  `tests/test_tasks.py`, which their prompts listed under READ FIRST as "reference only".
- Did any subagent's output break the next subagent's assumption? No. Both handoffs matched the
  agreed contract, B did not have to stop, and C found no defect, so there was nothing to recover.
- What would I change a second time? Write this document before opening Claude Code and in the
  six-field format from the start; record each pytest result beside the Output field when the
  subagent finishes; and give each subagent only its own section and prompt, so that the Input
  field is something the subagent cannot exceed.

One further observation: Subagent A wrote `services/users.py` with a shell heredoc
(`cat > services/users.py`), not with the Edit or Write tool. The file was inside A's boundary, so
no constraint was violated, but a hook that inspects only file-editing tools would not see a write
made this way.

Not repairable afterwards: this document was drafted in Claude Code, and the six-field table and
the pytest results beside Output were added after execution.
