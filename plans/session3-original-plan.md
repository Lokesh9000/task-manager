# PA5 Task 1 — Session 3: PATCH /api/tasks/<id> priority updates

## Context

Sessions 1 and 2 added `priority` (int 1–5, default 3) to the task store, to `create_task()`, and to `POST /api/tasks`. There is still no way to change the priority of an existing task. This session adds `PATCH /api/tasks/<id>` so clients can update it, with the same validation rules as creation, a 404 for unknown tasks, and a guarantee that rejected requests leave `TASKS` untouched.

## Current state (inspected)

- `services/tasks.py` — `create_task()` validates priority inline (rejects `bool`, non-`int`, out of range) and raises `ValidationError("priority", "must be an integer from 1 to 5")`. `get_task()` raises `NotFoundError("Task")`. Constants `MIN_PRIORITY`/`MAX_PRIORITY` exist. No update function.
- `routes/api.py` — thin routes; `@api.errorhandler(AppError)` already turns `ValidationError` into 422 and `NotFoundError` into 404 as `{"error": message}`. No PATCH route.
- `tests/test_tasks.py` — service tests; opt-in `restore_tasks` fixture (deepcopy snapshot, restore in `finally`).
- `tests/test_api.py` — API tests; `client` fixture and an **autouse** `restore_tasks` fixture.
- No existing test covers priority updates, so new tests are needed (none are modified or removed).

## Decision: a service-layer update function is needed

Add `update_task_priority()` to `services/tasks.py`. Reasons:

1. CLAUDE.md requires `routes/api.py → services/*.py → TASKS`; a route that mutates `TASKS[task_id]["priority"]` itself would break the layering and put task logic in the HTTP layer.
2. The priority rule already lives in the service (`create_task`). Validating in the route would duplicate it and let the two drift.
3. Errors must be `NotFoundError` / `ValidationError` raised from services; the existing error handler then produces the 404/422 with no new route error code.
4. It makes the "invalid input does not mutate" guarantee testable at the service level, independent of Flask.

## Implementation

### 1. `services/tasks.py`

- Add a private helper and use it from both `create_task()` and the new function, so there is one definition of a valid priority:

  ```python
  def _validate_priority(priority: int) -> None:
      """Validate a task priority.

      Args:
          priority: The priority value to validate.

      Raises:
          ValidationError: If priority is not an integer from 1 to 5.
      """
      if (isinstance(priority, bool) or not isinstance(priority, int)
              or not MIN_PRIORITY <= priority <= MAX_PRIORITY):
          raise ValidationError("priority", "must be an integer from 1 to 5")
  ```

  `create_task()` replaces its inline `if` with `_validate_priority(priority)` — same condition, same message, signature and docstring unchanged. Existing create tests guard this refactor.

- Add the public function (type hints + Google-style docstring per `services/users.py`):

  ```python
  def update_task_priority(task_id: int, priority: int) -> dict:
      """Update the priority of an existing task.

      Args:
          task_id: The unique identifier for the task.
          priority: The new priority from 1 (urgent) to 5 (low).

      Returns:
          The updated task record as a dictionary.

      Raises:
          NotFoundError: If no task exists with the given ID.
          ValidationError: If priority is not an integer from 1 to 5.
      """
      task = get_task(task_id)
      _validate_priority(priority)
      task["priority"] = priority
      return task
  ```

  Both checks run before the single assignment, so any failure leaves `TASKS` unmodified. Reuses `get_task()` for the lookup/404.

### 2. `routes/api.py`

- Extend the import: `from services.tasks import get_task, create_task, process_order, update_task_priority` (the existing unused `process_order` import is a pre-existing Ruff finding and is left alone).
- Add the route after `get_task_route`:

  ```python
  @api.route("/tasks/<int:task_id>", methods=["PATCH"])
  def update_task_route(task_id):
      data = request.get_json()
      return jsonify(update_task_priority(task_id, data.get("priority")))
  ```

  Returns 200 with the full updated task. `handle_app_error` and `utils/errors.py` are not touched.

## Validation and error handling

| Case | Result |
|---|---|
| `priority` is int 1–5, task exists | 200, updated task JSON |
| `priority` is `null`, `true`/`false`, `"3"`, `2.5`, `3.0`, `0`, `6`, `-1` | 422 `{"error": "Invalid priority: must be an integer from 1 to 5"}` |
| Task id not in `TASKS` | 404 `{"error": "Task not found"}` |
| Unknown task **and** invalid priority | 404 (lookup runs first) |

### Assumptions on behavior the requirements don't specify (please confirm on approval)

- **Body without a `priority` key (e.g. `{}`)** → treated like `null` → 422 with the same message. The endpoint exists only to update priority, so a body without one is invalid rather than a silent no-op.
- **Other keys in the body (`title`, `done`, `user_id`, `id`)** → ignored; only `priority` is updatable in this session.
- **404 before 422** when both apply.
- **Malformed JSON / missing JSON content type / non-object JSON body** → not handled specially; behaves as Flask does today, exactly like the existing POST route. Hardening that is outside this session's scope.

## Tests

### `tests/test_tasks.py` (service) — add, don't modify existing tests

Add `update_task_priority` to the existing import; every new test uses the existing `restore_tasks` fixture.

- `test_update_task_priority_valid` — parametrized over 1–5: returned task has the new priority, `TASKS[1]["priority"]` matches, returned dict `is TASKS[1]`.
- `test_update_task_priority_preserves_other_data` — after an update, task 1's `id`/`title`/`done`/`user_id` and tasks 2 and 3 equal a pre-update deepcopy.
- `test_update_task_priority_invalid` — parametrized `[0, 6, -1, "3", 2.5, 3.0, None, True, False]`: raises `ValidationError`, status 422, exact message, and `TASKS == deepcopy snapshot` taken before the call.
- `test_update_task_priority_missing_task` — id 999: raises `NotFoundError` ("Task not found", 404), `TASKS` equals snapshot and `999 not in TASKS`.

### `tests/test_api.py` (HTTP) — covered by the existing autouse `restore_tasks`

- `test_update_task_priority` — parametrized 1–5: `PATCH /api/tasks/1` → 200, body equals the original task with only `priority` changed, `TASKS[1]["priority"]` updated, and a follow-up `GET /api/tasks/1` returns the new priority.
- `test_update_task_priority_leaves_other_tasks_unchanged` — tasks 2 and 3 equal the pre-request snapshot.
- `test_update_task_invalid_priority` — parametrized `[None, True, False, "3", 2.5, 3.0, 0, 6, -1]`: 422, exact error body, `TASKS == snapshot`.
- `test_update_task_missing_priority` — body `{}`: 422, `TASKS == snapshot` (pins the assumption above).
- `test_update_task_not_found` — `PATCH /api/tasks/999` with a valid priority: 404, `{"error": "Task not found"}`, `TASKS == snapshot`.
- `test_update_task_not_found_with_invalid_priority` — 404, `TASKS == snapshot`.

### Test isolation

`TASKS` is a shared module-level dict, so every test that calls the update function or PATCH route runs under a snapshot/restore fixture (explicit in `test_tasks.py`, autouse in `test_api.py`). Integrity assertions compare against a `copy.deepcopy(TASKS)` taken inside the test, since a shallow copy would alias the mutated inner dicts. Tests always target seed task 1 and never depend on state left by another test.

## Files changed

- `services/tasks.py` — `_validate_priority()`, `update_task_priority()`, `create_task()` calls the helper.
- `routes/api.py` — import + PATCH route.
- `tests/test_tasks.py`, `tests/test_api.py` — new tests only.

Not touched: `utils/errors.py`, `app.py`, `services/users.py`, `requirements.txt`, `CLAUDE.md`, the error handler, the location of `TASKS`.

## Verification

1. Before editing: `python -m pytest -v` and `python -m ruff check .` to record the current pass count and Ruff finding count (CLAUDE.md says 6 findings; its "4 passing tests" figure predates sessions 1–2).
2. After editing: `python -m pytest -v` — all pre-existing tests still pass (proves POST/GET and `create_task` behavior is preserved) plus all new tests pass.
3. `python -m ruff check .` — finding count identical to step 1; no new findings, no unrelated cleanup.
4. `git status` / `git diff --stat` — only the four files above changed.
5. Report results as observed; no commit unless you ask for one.
