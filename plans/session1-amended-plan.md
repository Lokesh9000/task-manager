# PA 5 Task 1, Session 1: service-layer foundations for task priority

## Context

Tasks currently have `id`, `title`, `done`, `user_id` and no notion of urgency. This session adds a
`priority` integer (1 = most urgent, 5 = lowest, default 3) at the service layer only, so later
sessions can build routing/sorting on top of it. The layered flow
`routes/api.py` -> `services/tasks.py` -> `TASKS` stays as is.

Baseline measured before planning (read-only, no caches written):
- `pytest -q`: 6 passed
- `ruff check .`: 5 findings (`app.py` I001; `routes/api.py` I001 + F401; `tests/test_tasks.py` I001 + B017)
- `services/tasks.py` has no Ruff findings today.

Note: CLAUDE.md says "4 passing tests" and "6 Ruff findings"; the real numbers are 6 and 5.
CLAUDE.md is on the do-not-touch list, so this is only reported, not fixed.

## Files changed

Only `services/tasks.py` and `tests/test_tasks.py`. Nothing else.

## Changes in `services/tasks.py`

1. **Import** (line 2): `from utils.errors import NotFoundError, ValidationError`.

2. **New module constants** (above `TASKS`):
   `MIN_PRIORITY = 1`, `MAX_PRIORITY = 5`, `DEFAULT_PRIORITY = 3`.

3. **Data structure `TASKS`** (lines 4-8): add `"priority": 3` as the last key of each of the
   three seed records. IDs, titles, `done`, `user_id` unchanged. Still the same module-level dict.

4. **New private helper** `_validate_priority(priority: object) -> int`
   - Type hints + Google-style docstring (`Args`, `Returns`, `Raises`), per `services/users.py`.
   - Rejects when `type(priority) is not int` (exact type check, so `True`/`False`, `"3"`, `3.0`,
     `2.5`, `None` all fail; `isinstance` would wrongly accept booleans).
   - Rejects when not `MIN_PRIORITY <= priority <= MAX_PRIORITY`.
   - Both cases raise `ValidationError("priority", "must be an integer from 1 to 5")`
     -> message `"Invalid priority: must be an integer from 1 to 5"`, status 422 (existing mapping).
   - Returns the validated int.

5. **`create_task`** (lines 47-60): signature becomes
   `create_task(title: str, user_id: int, priority: int = DEFAULT_PRIORITY) -> dict`.
   - Backward compatible: the existing positional call in `routes/api.py:19`
     (`create_task(data["title"], data["user_id"])`) keeps working and yields priority 3.
   - Calls `_validate_priority(priority)` **before** computing `new_id` or writing to `TASKS`, so a
     rejected call leaves the store untouched.
   - Stores `"priority"` as the last key of the new record.
   - Docstring gains the `priority` arg and a `Raises: ValidationError` section.
   - The default is the literal 3, not a `None` sentinel, because an explicit `None` must be rejected.

Not changed: `process_order`, `get_task`, `get_tasks_for_user` (they return the stored dicts, so
they surface `priority` automatically).

## Changes in `tests/test_tasks.py`

No existing test covers `create_task` or priority, so new tests are needed. The 6 existing tests
are left untouched.

- Extend imports: `copy`; `TASKS`, `create_task` from `services.tasks`; `ValidationError`.
- Add a non-autouse fixture `restore_tasks` that deep-copies `TASKS`, then wraps `yield` in
  `try`/`finally`, with `TASKS.clear(); TASKS.update(snapshot)` in the `finally` block, so `TASKS`
  is restored even when the test fails. It mutates the existing dict in place (never rebinds
  `TASKS`), so the service module keeps the same object.
- **Amendment (approved review, session 1):** all four new priority tests request `restore_tasks`,
  including the read-only `test_seed_tasks_have_default_priority`, so every new test uses the same
  shared-state isolation. The six existing tests do not use the fixture and are not edited.
- New tests, appended at the end of the file (each takes `restore_tasks`):
  - `test_seed_tasks_have_default_priority`: tasks 1, 2, 3 each have `priority == 3`.
  - `test_create_task_default_priority`: omitted priority -> 3; other fields and next ID as before.
  - `test_create_task_explicit_priority`: parametrized over 1 and 5 (boundaries).
  - `test_create_task_invalid_priority`: parametrized over `True`, `False`, `"3"`, `3.0`, `2.5`,
    `0`, `6`, `-1`, `None`; asserts `ValidationError`, `status_code == 422`, the exact message,
    and that `TASKS` has the same keys afterwards.

## Assumptions (not inventing behavior)

- No "update priority" service function this session; only creation and seed data were requested.
- No new validation of `title` or `user_id` in `create_task` (it does not check either today).
- One shared error message for every invalid-priority case.
- `process_order` keeps its raw `KeyError`; out of scope.

## Compatibility and testing risks

- **API output changes without a route edit**: `GET /tasks/<id>` and `POST /tasks` responses now
  include `priority`, because routes `jsonify` the service dicts. Expected, but it is a visible change.
- **Priority not settable over HTTP yet**: the route does not pass it. A later session's route must
  distinguish "key omitted" (default 3) from explicit `null` (422); `data.get("priority")` would
  conflate them.
- **Shared mutable `TASKS` across tests**: `test_get_tasks_for_user_valid` asserts user 1's IDs are
  exactly `[1, 2]`. The `restore_tasks` fixture (used by all four new tests, restoring in a
  `finally` block) keeps new tests from leaking records regardless of test order or failures.
  It does not isolate the six existing tests from each other; `test_process_order_valid` still
  marks task 1 done for the rest of the run, as it does today.
- **Ruff**: the test file's import block already has I001; extending it keeps that one existing
  finding rather than adding one. No unrelated lint cleanup.
- **Exact type check** also rejects `int` subclasses (e.g. `IntEnum`); acceptable since inputs
  come from JSON.

## Verification

1. `.venv/Scripts/python -m pytest -q` -> expect 6 existing + 13 new = 19 passed.
2. `.venv/Scripts/python -m ruff check .` -> expect the same 5 findings, none new.
3. `git diff` -> only `services/tasks.py` and `tests/test_tasks.py`.
4. Report any difference between this plan and the actual result. No `PLAN_LOG.md` this session.
