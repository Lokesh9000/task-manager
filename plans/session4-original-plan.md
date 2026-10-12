# PA5 Task 1 — Session 4: optional `?priority=` filter on GET /api/tasks

Project: `C:\Users\Lokes\Desktop\task-manager-pa5-fresh` (branch `main`, clean, HEAD `1420231`).

## Context

Sessions 1–3 added a task `priority` (integer 1–5) to the service layer, POST and PATCH. Session 4 lets clients list tasks filtered by priority.

Inspection found that **`GET /api/tasks` does not exist yet**: `/api/tasks` only accepts POST, so GET returns 405, and there is no list-all service function. You confirmed the intended behavior:

- GET without `priority` returns all tasks.
- A repeated `priority` parameter is rejected with 422.

Baseline measured before planning: `73 passed`, Ruff `Found 5 errors` (3 I001, 1 B017, 1 F401). Flask 3.0.0, Werkzeug 3.1.8.

## Behavior

| Request | Response |
|---|---|
| `GET /api/tasks` | 200, JSON array of every task, in `TASKS` order (id ascending) |
| `GET /api/tasks?priority=3` | 200, JSON array of tasks whose `priority == 3` |
| Valid priority, no matches | 200, `[]` |
| Value not a plain decimal integer (`abc`, empty, `3.0`, `-1`, `+3`, ` 3`, `true`) | 422 `{"error": "Invalid priority: must be an integer from 1 to 5"}` |
| Integer out of range (`0`, `6`, `10`) | same 422 |
| `priority` given more than once, even with identical values | 422 `{"error": "Invalid priority: must be provided at most once"}` |
| Other query parameters (`?done=true`, `?Priority=3`) | ignored, all tasks returned |

Validation order: repeated-parameter check, then string-to-integer parsing (both in the route), then the 1–5 range check (service). All of it runs before any data is read, and nothing writes to `TASKS`.

## Changes

### `services/tasks.py`

- Add a constant next to `MIN_PRIORITY`/`MAX_PRIORITY`: `PRIORITY_REASON = "must be an integer from 1 to 5"`, and have `_validate_priority()` use it. The message text is unchanged; this lets the route reuse it without copying the string.
- Add `list_tasks`, placed after `get_tasks_for_user`, with type hints and a Google-style docstring (`Args`, `Returns`, `Raises`):

  ```python
  def list_tasks(priority: int | None = None) -> list[dict]:
      if priority is None:
          return list(TASKS.values())
      _validate_priority(priority)
      return [task for task in TASKS.values() if task["priority"] == priority]
  ```

  It reuses the existing `_validate_priority()`, so `True`, `"3"` and `3.0` are rejected at the service level exactly as in `create_task` and `update_task_priority`. It returns a new list each call and never assigns into `TASKS`. The records are the stored dicts, matching `get_tasks_for_user`.

No existing signature changes.

### `routes/api.py`

- Extend the existing import: add `list_tasks` and `PRIORITY_REASON` from `services.tasks`.
- Add a GET route on `/tasks`; the POST route is left as it is.

  ```python
  @api.route("/tasks", methods=["GET"])
  def list_tasks_route():
      values = request.args.getlist("priority")
      if not values:
          return jsonify(list_tasks())
      if len(values) > 1:
          raise ValidationError("priority", "must be provided at most once")
      raw = values[0]
      if not (raw.isascii() and raw.isdigit()):
          raise ValidationError("priority", PRIORITY_REASON)
      try:
          priority = int(raw)
      except ValueError:
          raise ValidationError("priority", PRIORITY_REASON) from None
      return jsonify(list_tasks(priority))
  ```

  Errors are raised as the existing `ValidationError` and converted by the existing `@api.errorhandler(AppError)`.

Not touched: `utils/errors.py`, the error handler, `app.py`, `services/users.py`, `requirements.txt`, `CLAUDE.md`, the POST/PATCH/GET-by-id routes, the location of `TASKS`, and the 5 existing Ruff findings.

## Edge cases

- **Empty value** (`?priority=`): the parameter is present but not an integer, so 422, not "no filter".
- **Leading zeros** (`?priority=03`): parsed as integer 3 and accepted. Say so if you want this rejected instead.
- **Non-ASCII digits** (`?priority=٣`): `int()` would accept these; the `isascii()` check rejects them with 422.
- **Very long digit strings**: `int()` raises `ValueError` beyond 4300 digits; the `try/except` turns that into 422 instead of a 500.
- **`+3`**: a literal `+` in a query string decodes to a space, and `%2B3` decodes to `+3`; both are 422.
- **HEAD/OPTIONS**: Flask adds these automatically for the new GET route. `/api/tasks/` with a trailing slash stays 404.
- **Seed data**: all three seed tasks have priority 3, so tests set up varied priorities themselves.

## Tests

No existing test is modified. Expected results are compared against the live `TASKS` rather than hard-coded seed dicts, because the existing `test_process_order_valid` leaves task 1 marked done.

### `tests/test_tasks.py` (service; each uses the existing `restore_tasks` fixture)

- `test_list_tasks_without_priority`: `list_tasks()` and `list_tasks(None)` both equal `list(TASKS.values())`.
- `test_list_tasks_with_priority`: set task 1 to priority 1 and task 2 to priority 5; parametrized over 1–5, expected ids `1→[1]`, `2→[]`, `3→[3]`, `4→[]`, `5→[2]`.
- `test_list_tasks_invalid_priority`: parametrized `[0, 6, -1, "3", 2.5, 3.0, True, False]`; `ValidationError`, status 422, exact message, `TASKS == snapshot`.
- `test_list_tasks_does_not_modify_tasks`: deep-copy snapshot, call unfiltered and filtered, clear the returned list, assert `TASKS == snapshot`.

### `tests/test_api.py` (HTTP; the autouse `restore_tasks` fixture already isolates every test)

- `test_list_tasks_without_priority`: 200, body equals `list(TASKS.values())`, `TASKS == snapshot`.
- `test_list_tasks_with_priority`: same setup and 1–5 parametrization as the service test; 200 and expected ids.
- `test_list_tasks_no_matches`: `?priority=1` on seed data returns 200 `[]`.
- `test_list_tasks_after_patch`: PATCH task 1 to 5, then `?priority=5` returns only task 1 and `?priority=3` no longer includes it.
- `test_list_tasks_invalid_priority`: parametrized `["abc", "", "3.0", "2.5", "0", "6", "-1", "+3", " 3", "3 ", "true", "null", "1,2", "٣", "9" * 5000]`, sent with `query_string={"priority": value}`; 422, exact body, `TASKS == snapshot`.
- `test_list_tasks_repeated_priority`: parametrized raw query strings `priority=1&priority=2`, `priority=3&priority=3`, `priority=3&priority=abc`, `priority=abc&priority=3`, `priority=&priority=3`; 422 with the "at most once" body, `TASKS == snapshot`.
- `test_list_tasks_ignores_other_params`: `?done=true` and `?Priority=3` return all tasks.

## Verification

Run from `C:\Users\Lokes\Desktop\task-manager-pa5-fresh`:

1. `python -m pytest -v`: the 73 existing tests still pass and all new tests pass.
2. `python -m pytest -v tests/test_tasks.py -k list_tasks` and `python -m pytest -v tests/test_api.py -k list_tasks`: the new tests in isolation.
3. `python -m ruff check .`: still `Found 5 errors`.
4. `git status --short` and `git diff --stat`: only `services/tasks.py`, `routes/api.py`, `tests/test_tasks.py`, `tests/test_api.py` changed.

No commit or push. `PLAN_LOG.md`, `ITERATION_LOG.md` and `plans/` are left alone unless you ask me to update them.
