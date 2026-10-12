# PA 5, Task 1, Session 1 — task priority (service layer)

## Context

Tasks need a `priority` field: an integer 1–5 (1 = urgent, 5 = low), optional at creation with a default of 3. Every task, including the three seed tasks, must carry one. This session covers the service layer only; routes come later, so `routes/api.py` keeps calling `create_task(data["title"], data["user_id"])` unchanged and must keep working.

## Files changed

Only `services/tasks.py` and `tests/test_tasks.py`. Nothing else.

## `services/tasks.py`

1. **Import**: `from utils.errors import NotFoundError, ValidationError`.

2. **Constants** (module level, next to `TASKS`):
   `MIN_PRIORITY = 1`, `MAX_PRIORITY = 5`, `DEFAULT_PRIORITY = 3`.

3. **Seed data**: add `"priority": 3` to each of the three entries in `TASKS`.
   The spec gives no per-task values, so all three get the default rather than invented ones.

4. **`create_task`**: new signature
   `create_task(title: str, user_id: int, priority: int = DEFAULT_PRIORITY) -> dict`
   - Added as a trailing parameter with a default, so the existing two-argument call in `routes/api.py:19` is unaffected.
   - Validate before touching `TASKS`, so a rejected call stores nothing:
     ```python
     if isinstance(priority, bool) or not isinstance(priority, int):
         raise ValidationError("priority", "must be an integer from 1 to 5")
     if not MIN_PRIORITY <= priority <= MAX_PRIORITY:
         raise ValidationError("priority", "must be an integer from 1 to 5")
     ```
     (written as one combined condition, validation inline as in `create_user` in `services/users.py`)
   - Store `"priority": priority` in the new record.
   - Docstring: add `priority` to `Args` and a `Raises: ValidationError` section, Google style as in `services/users.py`.

No other function changes. `get_task` and `get_tasks_for_user` return the stored dicts, so they expose `priority` automatically.

## `tests/test_tasks.py`

The 6 existing tests stay as they are; none covers priority. Add `create_task`, `TASKS` and `ValidationError` to the existing imports and append:

| Test | Asserts |
|---|---|
| `test_seed_tasks_have_priority` | every task in `TASKS` has an int `priority` within 1–5 |
| `test_create_task_default_priority` | `create_task("x", 1)` → `priority == 3` (also proves the old two-argument call still works) |
| `test_create_task_with_priority` | `create_task("x", 1, 1)` and `priority=5` are stored as given (both boundaries) |
| `test_create_task_invalid_priority` | parametrized over `0, 6, -1, "3", 2.5, None, True` → `ValidationError`, `status_code == 422`, message `"Invalid priority: must be an integer from 1 to 5"`, and `len(TASKS)` unchanged |

Tests that create tasks assert on the returned record, not on a specific new ID, so they do not depend on test order.

## Assumptions (spec is silent — say so if you want otherwise)

- **Non-integers are rejected, not coerced**: `"3"`, `2.5`, `None` and `True`/`False` all raise `ValidationError`. `bool` is called out because Python treats `True` as the integer 1.
- **Explicit `None` is invalid**; "optional" means the argument may be omitted, not passed as `None`.
- **Seed tasks all get priority 3.**
- **No update function** for priority is added; the request only covers creation and seed data.
- **No new validation of `title` or `user_id`** in `create_task`, and `process_order`'s raw `KeyError` is left alone; both are outside this task.

## Verification

```
.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m ruff check .
```

Expected: 16 passed (6 existing + 3 + 7 parametrized cases), and Ruff still at 5 findings with none new. I will run both before editing to confirm the 6 passed / 5 findings baseline (CLAUDE.md still says 4 and 6), then after, and report the actual output.
