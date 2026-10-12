# PA5 Task 1, Session 2 — `POST /api/tasks` priority support

## Context

Session 1 (commit `309a4ef`) added priority to the service layer: `create_task(title, user_id, priority=DEFAULT_PRIORITY)` in `services/tasks.py` validates the value (rejects bools, non-ints, and anything outside 1–5 with `ValidationError("priority", "must be an integer from 1 to 5")`) and stores it on the task. The route never passes priority through, so API clients cannot set it. This session wires the route to the existing service behavior — no new validation logic.

Current route (`routes/api.py:16-19`):

```python
data = request.get_json()
return jsonify(create_task(data["title"], data["user_id"])), 201
```

## File boundaries

| File | Change |
|---|---|
| `routes/api.py` | Edit `create_task_route` only |
| `tests/test_api.py` | **New** — API-level tests |
| `services/tasks.py`, `utils/errors.py`, `app.py`, `tests/test_tasks.py`, `requirements.txt` | Untouched |

Why a new test file: no API tests exist today; `tests/test_tasks.py` holds service tests and already covers the service-side priority rules, so it needs no change (per the CLAUDE.md "check existing coverage first" rule). The new file needs its own small `TASKS` snapshot/restore fixture, since importing `restore_tasks` from `tests/test_tasks.py` would trigger new Ruff findings (F401/F811) and there is no `conftest.py`.

## Implementation — `routes/api.py`

Replace the body of `create_task_route` with:

```python
data = request.get_json()
if "priority" in data:
    task = create_task(data["title"], data["user_id"], data["priority"])
else:
    task = create_task(data["title"], data["user_id"])
return jsonify(task), 201
```

Key points:

- **Key presence, not `data.get("priority")`.** `.get()` would turn an explicit `null` into "omitted" and silently default to 3. Checking `in` forwards `None` to the service, which rejects it.
- **Default stays in the service.** The route does not import or repeat `DEFAULT_PRIORITY`; omitting the argument lets `create_task` apply it.
- **No validation in the route.** Raw JSON values go straight to `create_task`. JSON `true`/`false` → `bool`, `"3"` → `str`, `2.5` and `3.0` → `float`, `null` → `None`; all are rejected by the existing service check.
- **Response** is the stored task dict, which already includes `priority`.
- Imports are unchanged (the unused `process_order` import is an existing Ruff finding and is left alone).

## Error handling

- Invalid priority → service raises `ValidationError` → existing `@api.errorhandler(AppError)` returns `422` with `{"error": "Invalid priority: must be an integer from 1 to 5"}`. No handler or status-mapping changes.
- Validation runs before the `TASKS` write, so a rejected request stores nothing.
- Unchanged, out of scope: missing `title`/`user_id` and non-object bodies still fail exactly as they do today (unhandled `KeyError`/`TypeError`). Title and user_id validation is not added.

## Tests — `tests/test_api.py`

Fixtures: `client` (`app.test_client()` from `app.py`) and a local snapshot/restore of `TASKS` (same pattern as `restore_tasks` in `tests/test_tasks.py`), applied to every test.

| Test | Request | Expect |
|---|---|---|
| `test_create_task_without_priority` | `{"title", "user_id"}` | 201; body has `priority == 3`, plus `id`, `title`, `user_id`, `done is False`; `TASKS[id]["priority"] == 3` |
| `test_create_task_with_priority` (param `1, 2, 3, 4, 5`) | adds `"priority": n` | 201; body `priority == n`; stored value `== n` |
| `test_create_task_invalid_priority` (param `None, True, False, "3", 2.5, 3.0, 0, 6, -1`) | adds `"priority": bad` | 422; body `== {"error": "Invalid priority: must be an integer from 1 to 5"}`; `len(TASKS)` unchanged |

`None` is sent as JSON `null` by the test client, covering the explicit-null case; `3.0` confirms whole-number floats are rejected too.

## Verification

1. Before editing: run `python -m pytest -v` and `python -m ruff check .` to record the actual baselines (CLAUDE.md says 4 tests / 6 findings; Session 1 added tests, so the test count will be higher).
2. After editing: `python -m pytest -v` — all prior tests still pass, plus 15 new cases in `tests/test_api.py`.
3. `python -m ruff check .` — finding count identical to the baseline; nothing new from `routes/api.py` or `tests/test_api.py`.
4. `git status` / `git diff --stat` — only `routes/api.py` modified and `tests/test_api.py` added.

No commit unless requested.
