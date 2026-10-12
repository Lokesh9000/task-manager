# PA 5 Task 1, Session 4: priority filtering on GET /api/tasks

## Context

Sessions 1-3 added a `priority` field (1-5, default 3), exposed it on `POST /api/tasks`, and
added `PATCH /api/tasks/<id>`. This session adds a way to list tasks, optionally filtered with
`?priority=n`.

## Finding that changes the premise: there is nothing to preserve yet

The prompt says to inspect "the existing `list_tasks` service and `GET /api/tasks` route". Neither
exists at `d4b4f0c`:

- `services/tasks.py` has `process_order`, `get_task`, `get_tasks_for_user`, `create_task`,
  `update_task_priority`. No `list_tasks`.
- `routes/api.py` registers `/tasks` for `POST` only. `GET /api/tasks` currently returns 405.
- No code in the repo reads `request.args`, so there is no query-parameter convention either.

**Assumption (please confirm or amend):** this session creates both the service function and the
route. "Existing behavior" in requirement 1 is read as "the unfiltered call returns every task".
Two things then have no precedent and are my choices:

1. **Response shape:** a bare JSON array of task objects, in `TASKS` insertion order. Every
   existing route returns `jsonify(<service result>)` with no envelope, so this follows suit.
2. **Signature compatibility:** there is no prior `list_tasks` signature to break. The new one is
   `list_tasks(priority: int | None = None)`, so `list_tasks()` works with no arguments.

## Files to change

Only `services/tasks.py`, `routes/api.py`, `tests/test_tasks.py`.

## 1. `services/tasks.py`: two new functions

Appended after `update_task_priority`. Nothing existing is edited.

```python
def parse_priority_filter(values: list[str]) -> int | None:
    """Parse the raw priority filter values from a task listing request.

    Args:
        values: Every raw string supplied for the priority filter. An empty
            list means no filter was requested.

    Returns:
        The requested priority, or None if no filter was requested.

    Raises:
        ValidationError: If more than one value is supplied, or the value is
            not exactly one of the strings "1" to "5". Empty strings, padded
            values, signs, leading zeros, and decimals are rejected.
    """
    if not values:
        return None
    if len(values) != 1 or values[0] not in _PRIORITY_FILTER_VALUES:
        raise ValidationError("priority", "must be an integer from 1 to 5")
    return _PRIORITY_FILTER_VALUES[values[0]]

def list_tasks(priority: int | None = None) -> list[dict]:
    """Retrieve all tasks, optionally filtered by priority.

    Args:
        priority: If given, only tasks with this priority are returned.
            Defaults to None, which returns every task.

    Returns:
        A new list of task records. The list is empty if no task matches.

    Raises:
        ValidationError: If priority is given and is not an integer from 1 to 5.
    """
    if priority is None:
        return list(TASKS.values())
    priority = _validate_priority(priority)
    return [task for task in TASKS.values() if task["priority"] == priority]
```

Plus one module constant next to the existing three:

```python
_PRIORITY_FILTER_VALUES = {str(p): p for p in range(MIN_PRIORITY, MAX_PRIORITY + 1)}
```

### Validation decisions

- **Strings are matched, never converted with `int()`.** `int()` accepts `" 3 "`, `"+3"`, `"03"`,
  `"1_0"` and non-ASCII digits such as `"٣"`, and raises a plain `ValueError` (a 500) on digit
  strings longer than 4300 characters. An exact lookup in a table built from
  `MIN_PRIORITY`/`MAX_PRIORITY` avoids all of that and keeps the range defined in one place.
- **`list_tasks` reuses `_validate_priority`** (`services/tasks.py:14`), so a direct service call
  with `True`, `"3"`, `3.0`, `0` or `6` is rejected exactly as in `create_task`.
- **Same error message everywhere:** `Invalid priority: must be an integer from 1 to 5`, 422,
  through the existing `ValidationError` and error handler. No change to `utils/errors.py`.
- **Repeated parameter (`?priority=1&priority=2`) is rejected** with the same 422 rather than
  silently using the first value. This is my reading of "malformed values"; say so if you would
  rather the first value win.
- **Leading zeros (`03`) are rejected** as non-canonical. Same caveat.
- Unknown query parameters (`?foo=1`) are ignored, which is Flask's default. No new behaviour.

## 2. `routes/api.py`: one new route

Import `list_tasks` and `parse_priority_filter` on the existing `services.tasks` import line, and
add next to the other `/tasks` routes:

```python
@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    return jsonify(list_tasks(parse_priority_filter(request.args.getlist("priority"))))
```

The route only extracts the query parameter and serialises. `getlist` returns `[]` when the
parameter is absent, `[""]` for `?priority=` or bare `?priority`. POST, PATCH, `GET /tasks/<id>`
and the error handler are untouched.

## 3. `tests/test_tasks.py`: new tests, all using `restore_tasks`

Add `list_tasks, parse_priority_filter` to the import line. The 67 existing cases are not edited.
No existing test covers listing, so all of these are new coverage.

Service level (38 cases):

| Test | Cases | Asserts |
|---|---|---|
| `test_list_tasks_unfiltered` | 1 | `list_tasks()` and `list_tasks(None)` both equal `list(TASKS.values())`, ids `[1, 2, 3]` |
| `test_list_tasks_matching_seeded` | 1 | `list_tasks(3)` ids `[1, 2, 3]` |
| `test_list_tasks_no_match` | 4: `1, 2, 4, 5` | returns `[]` |
| `test_list_tasks_created_and_updated` | 1 | after `create_task(..., 1)` and `update_task_priority(2, {"priority": 5})`: filter 1 is the new task, 5 is id 2, 3 is ids `[1, 3]` |
| `test_list_tasks_invalid_priority` | 8: `True, False, "3", 3.0, 2.5, 0, 6, -1` | `ValidationError`, 422, message, `TASKS` equals deep copy |
| `test_list_tasks_does_not_mutate` | 1 | `TASKS` equals deep copy after unfiltered, matching and empty calls; clearing the returned list leaves `TASKS` intact |
| `test_parse_priority_filter_valid` | 6: `[]`→`None`, `["1"]`..`["5"]`→1..5 | return value |
| `test_parse_priority_filter_invalid` | 16: `[""]`, `["0"]`, `["6"]`, `["-1"]`, `["3.0"]`, `["2.5"]`, `["true"]`, `["abc"]`, `[" 3"]`, `["3 "]`, `["03"]`, `["+3"]`, `["٣"]`, `["9" * 5000]`, `["1", "2"]`, `["3", "3"]` | `ValidationError`, 422, message |

API level through `client` (22 cases):

| Test | Cases | Asserts |
|---|---|---|
| `test_api_list_tasks_unfiltered` | 1 | 200, body equals `list(TASKS.values())` with all five fields |
| `test_api_list_tasks_matching_seeded` | 1 | `?priority=3` → 200, ids `[1, 2, 3]` |
| `test_api_list_tasks_no_match` | 4: `1, 2, 4, 5` | 200, `[]` |
| `test_api_list_tasks_created_and_updated` | 1 | POST a priority-1 task and PATCH task 2 to 5, then filters 1, 5, 3 return the expected ids |
| `test_api_list_tasks_invalid_priority` | 14 query strings: `priority=`, `priority`, `priority=0`, `priority=6`, `priority=-1`, `priority=3.0`, `priority=2.5`, `priority=true`, `priority=abc`, `priority=%203`, `priority=3%20`, `priority=+3`, `priority=03`, `priority=1&priority=2` | 422, `{"error": "Invalid priority: must be an integer from 1 to 5"}`, `TASKS` equals deep copy |
| `test_api_list_tasks_does_not_mutate` | 1 | `TASKS` equals deep copy after unfiltered, matching and empty requests |

Expected total: 67 + 60 = 127 passing.

## Edge cases and risks

- **405 becomes 200.** `GET /api/tasks` stops returning 405. No existing test asserts the 405.
- **Two view functions on `/tasks`** (GET and POST) is standard Flask; POST dispatch is unchanged
  and is re-verified by the existing POST tests.
- **`/tasks` vs `/tasks/<int:task_id>`** do not overlap; `/api/tasks/` (trailing slash) stays 404.
- **Returned dicts are the stored records**, not copies, matching `get_task` and
  `get_tasks_for_user`. The list itself is new, so callers cannot alter `TASKS` membership through
  it. Deep-copying would diverge from the existing services, so it is not done.
- **`+` in a query string decodes to a space**, so `?priority=+3` arrives as `" 3"` and is
  rejected; covered by a test.
- **Shared state:** every new test takes `restore_tasks`, including the read-only ones, per the
  Session 1 amendment.
- **Ruff:** the test import line grows; earlier sessions showed line length is not a reported
  rule here. Baseline is re-measured before editing and compared after.

## Verification

1. `.venv/Scripts/python -m ruff check .` before editing, to record the baseline (expected 5).
2. `.venv/Scripts/python -m pytest -q` → 127 passed.
3. `.venv/Scripts/python -m ruff check .` → same findings as step 1, none new.
4. `git diff --check` → no output; `git status --short` → only the three allowed files.
5. No commit, no push. `PLAN_LOG.md` and `plans/` are left for you to update.
