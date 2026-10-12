# PA 5, Task 1, Session 1 — task priority (service layer) — revised

## Context

Tasks need a `priority` field: an integer 1–5 (1 = urgent, 5 = low), optional at creation with a default of 3. Every task, including the three seed tasks, must carry one. This session covers the service layer only; routes come later, so `routes/api.py` keeps calling `create_task(data["title"], data["user_id"])` unchanged and must keep working.

**Amendment in this revision:** the new tests call `create_task()`, which writes to the shared module-level `TASKS` dict. Avoiding fixed IDs did not stop that state leaking into later tests. A `restore_tasks` fixture now isolates every new test that can mutate `TASKS`. The `services/tasks.py` section is unchanged from the original plan.

## Files changed

Only `services/tasks.py` and `tests/test_tasks.py`. Nothing else. (`plans/session1-original-plan.md` stays as saved.)

## `services/tasks.py` (unchanged from the original plan)

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
     if (isinstance(priority, bool) or not isinstance(priority, int)
             or not MIN_PRIORITY <= priority <= MAX_PRIORITY):
         raise ValidationError("priority", "must be an integer from 1 to 5")
     ```
     (validation inline, as in `create_user` in `services/users.py`)
   - Store `"priority": priority` in the new record.
   - Docstring: add `priority` to `Args` and a `Raises: ValidationError` section, Google style as in `services/users.py`.

No other function changes. `get_task` and `get_tasks_for_user` return the stored dicts, so they expose `priority` automatically.

## `tests/test_tasks.py`

### Existing tests

The 6 existing test functions are left byte-for-byte unchanged, and none of them gets the fixture. Only the import block at the top changes: add `import copy`, and add `TASKS`, `create_task` and `ValidationError` to the two existing `from` imports.

### New fixture

```python
@pytest.fixture
def restore_tasks():
    snapshot = copy.deepcopy(TASKS)
    try:
        yield
    finally:
        TASKS.clear()
        TASKS.update(snapshot)
```

- **Not `autouse`**: it is requested by name only by the new tests that can mutate `TASKS`, so existing tests behave exactly as before.
- **`deepcopy`**: task records are mutable dicts, so a shallow copy would not protect against in-place edits to a record.
- **Restore in place** (`clear()` + `update()`), never by rebinding: `services/tasks.py` and the test module both hold a reference to the same dict object, and rebinding would leave the service using the mutated one.
- **`try/finally`** around the `yield`, so restoration runs when the test fails or errors.
- **Snapshot is taken at the start of each test that uses it**, and restored to that same state afterwards. See the first assumption below.

### New tests

| Test | Uses `restore_tasks` | Cases | Asserts |
|---|---|---|---|
| `test_seed_tasks_have_priority` | no (read-only) | 1 | every task in `TASKS` has an int `priority` within 1–5 |
| `test_create_task_default_priority` | yes | 1 | `create_task("x", 1)` → `priority == 3`, and the record is stored in `TASKS` (also proves the old two-argument call still works) |
| `test_create_task_with_priority` | yes | 1 | `create_task("x", 1, 1)` and `create_task("x", 1, priority=5)` are stored as given (both boundaries, one test function) |
| `test_create_task_invalid_priority` | yes | 7 | parametrized over `0, 6, -1, "3", 2.5, None, True` → `ValidationError`, `status_code == 422`, message `"Invalid priority: must be an integer from 1 to 5"`, and `len(TASKS)` unchanged |

`test_create_task_invalid_priority` mutates nothing when the code is correct, but it would if validation were broken, so it takes the fixture too. That keeps one failing test from causing knock-on failures in others.

### Order independence

- Each mutating new test starts from, and returns `TASKS` to, the state it found, so no new test sees another's tasks, in any order.
- No new test asserts on a specific new ID or on the total number of tasks.
- `test_seed_tasks_have_priority` checks every record present. Because the mutating tests clean up after themselves, that is always just the seed tasks, wherever it runs.
- The one pre-existing leak stays: `test_process_order_valid` sets task 1's `done` to `True` and is not allowed to change. No new test reads `done`, so this cannot affect them.

### Expected test count

| Source | Collected items |
|---|---|
| Existing tests | 6 |
| `test_seed_tasks_have_priority` | 1 |
| `test_create_task_default_priority` | 1 |
| `test_create_task_with_priority` | 1 |
| `test_create_task_invalid_priority` (7 parameters) | 7 |
| **Total** | **16** |

The 7 comes from counting the parameter list itself: `0`, `6`, `-1`, `"3"`, `2.5`, `None`, `True`. The count of 6 existing tests is from reading the file (6 `test_` functions, none parametrized). I will confirm 16 against `pytest --collect-only -q` rather than rely on this arithmetic.

## Assumptions (spec is silent — say so if you want otherwise)

- **"Original state" means the state when each test starts**, not the state at import. Restoring to import-time state would also undo the `done` change left by the existing `test_process_order_valid`, which changes what existing tests leave behind; snapshot-per-test leaves existing behavior exactly as it is.
- **Non-integers are rejected, not coerced**: `"3"`, `2.5`, `None` and `True`/`False` all raise `ValidationError`. `bool` is called out because Python treats `True` as the integer 1.
- **Explicit `None` is invalid**; "optional" means the argument may be omitted, not passed as `None`.
- **Seed tasks all get priority 3.**
- **No update function** for priority is added; the request only covers creation and seed data.
- **No new validation of `title` or `user_id`** in `create_task`, and `process_order`'s raw `KeyError` is left alone; both are outside this task.

## Verification

1. Before editing, confirm the baseline (expected 6 passed, 5 Ruff findings; `CLAUDE.md` still says 4 and 6):
   ```
   .venv/Scripts/python -m pytest -q
   .venv/Scripts/python -m ruff check .
   ```
2. After editing:
   - `.venv/Scripts/python -m pytest --collect-only -q` → 16 items.
   - `.venv/Scripts/python -m pytest -q` → 16 passed.
   - Order check with no new dependency: run the new tests alone, then run the whole file with the test node IDs listed in reverse order on the command line (pytest runs them in the order given). Both must pass.
   - `.venv/Scripts/python -m ruff check .` → still 5 findings, none new.
   - `git status --short` → only `services/tasks.py`, `tests/test_tasks.py` and the already-untracked `plans/`.
3. Report the actual command output, including any failure.
