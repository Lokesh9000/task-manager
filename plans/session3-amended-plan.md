# PA5 Task 1 — Session 3 (amended): PATCH /api/tasks/<id> priority updates

## What changed from the original plan

- The route now checks the body shape before touching `data`, so JSON `null`, arrays and other non-object bodies get a controlled 422 instead of an `AttributeError` (500).
- A missing `priority` key is rejected explicitly in the route rather than falling through as `None`.
- Three assumptions are revised (see "Decisions to confirm").
- API tests are added for `{}`, JSON `null` and JSON arrays, each asserting `TASKS` is unchanged.

## Service layer: `services/tasks.py` (unchanged from the original plan)

- Add `_validate_priority(priority: int) -> None`, holding the existing condition and message from `create_task()`.
- `create_task()` calls the helper instead of its inline `if`; its signature, docstring and behavior stay the same.
- Add `update_task_priority(task_id: int, priority: int) -> dict`:

  ```python
  task = get_task(task_id)        # NotFoundError -> 404
  _validate_priority(priority)    # ValidationError -> 422
  task["priority"] = priority
  return task
  ```

Body shape is an HTTP concern, so it stays out of the service. The service still takes a priority value and remains the only place that defines a valid one.

## Route: `routes/api.py`

- Extend the imports:
  - `from services.tasks import get_task, create_task, process_order, update_task_priority`
  - `from utils.errors import AppError, ValidationError`
- Add the route after `get_task_route`:

  ```python
  @api.route("/tasks/<int:task_id>", methods=["PATCH"])
  def update_task_route(task_id):
      data = request.get_json()
      if not isinstance(data, dict):
          raise ValidationError("request body", "must be a JSON object")
      if "priority" not in data:
          raise ValidationError("priority", "is required")
      return jsonify(update_task_priority(task_id, data["priority"]))
  ```

The two new errors are raised as the existing `ValidationError` and converted by the existing `@api.errorhandler(AppError)`. `utils/errors.py`, the handler and the status mapping are not touched, and no new error class is added.

## Validation order and responses

| Step | Check | Where | Failure response |
|---|---|---|---|
| 1 | Body is a JSON object | route | 422 `{"error": "Invalid request body: must be a JSON object"}` |
| 2 | `priority` key present | route | 422 `{"error": "Invalid priority: is required"}` |
| 3 | Task exists | service | 404 `{"error": "Task not found"}` |
| 4 | Priority is an int from 1 to 5 (not `bool`) | service | 422 `{"error": "Invalid priority: must be an integer from 1 to 5"}` |
| 5 | Assign and return | service | 200 with the full updated task |

All four checks run before the single assignment, so any rejected request leaves `TASKS` unmodified.

Unchanged behavior:
- Valid updates return 200 with the updated task.
- `null`, `true`/`false`, `"3"`, `2.5`, `3.0`, `0`, `6`, `-1` as the priority value return 422 with the existing message.
- An unknown task with a valid priority returns 404.
- An unknown task with an invalid priority value still returns 404, because the lookup runs before value validation.

## Decisions to confirm

1. **Message for a missing key.** `{}` returns `Invalid priority: is required`, distinct from the message for a present-but-invalid value. The alternative is to reuse `must be an integer from 1 to 5`, as the original plan did, but that means duplicating the service's message string in the route.
2. **Body-shape errors come before the 404.** `PATCH /api/tasks/999` with `[]` or `{}` returns 422, not 404, because the route checks the body before calling the service. Keeping 404 first would need an extra `get_task()` call in the route purely for ordering; I don't recommend it.
3. **Other keys in the body** (`title`, `done`, `user_id`, `id`) are still ignored.
4. **Malformed JSON or a missing JSON content type** is still out of scope. `request.get_json()` rejects these itself, exactly as the POST route does today. I have not checked the exact status codes Flask returns here.

## Tests

### `tests/test_tasks.py` (service): unchanged from the original plan

All four use the existing `restore_tasks` fixture; no existing tests are modified.

- `test_update_task_priority_valid`: parametrized 1–5.
- `test_update_task_priority_preserves_other_data`
- `test_update_task_priority_invalid`: parametrized `[0, 6, -1, "3", 2.5, 3.0, None, True, False]`; asserts `TASKS == snapshot`.
- `test_update_task_priority_missing_task`: id 999.

### `tests/test_api.py` (HTTP)

Kept from the original plan:
- `test_update_task_priority`: parametrized 1–5; 200, only `priority` changed, follow-up GET agrees.
- `test_update_task_priority_leaves_other_tasks_unchanged`
- `test_update_task_invalid_priority`: parametrized `[None, True, False, "3", 2.5, 3.0, 0, 6, -1]`; 422, exact body, `TASKS == snapshot`.
- `test_update_task_not_found`: 404, exact body, `TASKS == snapshot`.
- `test_update_task_not_found_with_invalid_priority`: 404, `TASKS == snapshot`.

Changed or new:
- `test_update_task_empty_object` replaces the original `test_update_task_missing_priority`. Body `{}` returns 422 with `{"error": "Invalid priority: is required"}`, and `TASKS == snapshot`.
- `test_update_task_json_null` (new). Body `null` returns 422 with `{"error": "Invalid request body: must be a JSON object"}`, and `TASKS == snapshot`.
  - It is sent as `data="null", content_type="application/json"`, because the test client's `json=None` sends no body at all.
- `test_update_task_json_array` (new), parametrized over `[]` and `[{"priority": 2}]`. Same 422 body, and `TASKS == snapshot`.
- `test_update_task_not_found_with_non_object_body` (new). `PATCH /api/tasks/999` with `[]` returns 422 and `TASKS == snapshot`; this pins decision 2.

### Test isolation

- Every PATCH test runs under the existing autouse `restore_tasks` fixture in `test_api.py`.
- Each rejection test takes `copy.deepcopy(TASKS)` before the request and asserts full equality afterwards, not just a length check.
- Tests target seed task 1 (or id 999) and never depend on state from another test.

## Files changed

- `services/tasks.py`: `_validate_priority()`, `update_task_priority()`, `create_task()` calls the helper.
- `routes/api.py`: two import lines and the PATCH route.
- `tests/test_tasks.py`, `tests/test_api.py`: new tests only.

Not touched: `utils/errors.py`, the error handler, `app.py`, `services/users.py`, `requirements.txt`, `CLAUDE.md`, the location of `TASKS`, the POST route.

## Verification

1. Before editing, run `python -m pytest -v` and `python -m ruff check .` to record the current pass count and Ruff finding count.
2. After editing, run `python -m pytest -v`: all pre-existing tests still pass and all new tests pass.
3. Run `python -m ruff check .`: the finding count matches step 1.
4. Run `git status` and `git diff --stat`: only the four files above changed.
5. Report results as observed; no commit unless you ask for one.
