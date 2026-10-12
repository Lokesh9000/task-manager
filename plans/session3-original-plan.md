# PA 5 Task 1, Session 3: PATCH /api/tasks/<id> to update task priority

## Context

Sessions 1 and 2 added a validated `priority` field (1 to 5, default 3) to tasks and exposed it
on `POST /api/tasks`. There is still no way to change the priority of an existing task. This
session adds `PATCH /api/tasks/<id>`, which accepts `{"priority": <int 1-5>}`, updates the task
in the in-memory `TASKS` store, and returns the full updated task. Invalid requests must return
422 (or 404 for an unknown task) and must leave `TASKS` untouched.

Checkpoint: commit `246b401`, 31 passing tests, 5 pre-existing Ruff findings.

## Files to change

Only these three: `services/tasks.py`, `routes/api.py`, `tests/test_tasks.py`.

## 1. `services/tasks.py`: new `update_task_priority`

Add one function after `create_task`. No existing function or signature changes.

```python
def update_task_priority(task_id: int, updates: object) -> dict:
    """Update the priority of an existing task.

    Args:
        task_id: The unique identifier for the task.
        updates: The requested changes. Must be a dictionary containing
            only the key "priority".

    Returns:
        The updated task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
        ValidationError: If updates is not a dictionary, contains a field
            other than priority, omits priority, or priority is not an
            integer from 1 to 5.
    """
    task = get_task(task_id)
    if type(updates) is not dict:
        raise ValidationError("request", "must be a JSON object")
    if any(field != "priority" for field in updates):
        raise ValidationError("request", "only priority can be updated")
    if "priority" not in updates:
        raise ValidationError("priority", "is required")
    task["priority"] = _validate_priority(updates["priority"])
    return task
```

Reuse:
- `get_task` (`services/tasks.py:37`) for the lookup and `NotFoundError("Task")`.
- `_validate_priority` (`services/tasks.py:14`) for the value check; no new priority rule is
  written anywhere.
- `ValidationError` (`utils/errors.py:11`), unchanged, for all 422 cases.

Why the service takes the whole payload: requirement 6 (missing priority, empty object,
unsupported fields) is validation. Putting it in the service keeps every rule in one place and
leaves the route with no validation code at all.

Validation behaviour, in order (first failure wins):

| # | Condition | Result | Response body `error` |
|---|---|---|---|
| 1 | task ID not in `TASKS` | 404 | `Task not found` |
| 2 | body is not a JSON object (list, string, number, null) | 422 | `Invalid request: must be a JSON object` |
| 3 | any key other than `priority` (including `id`, `title`, `done`, `user_id`) | 422 | `Invalid request: only priority can be updated` |
| 4 | `priority` key absent (this is the `{}` case) | 422 | `Invalid priority: is required` |
| 5 | priority is null, bool, string, float, or outside 1 to 5 | 422 | `Invalid priority: must be an integer from 1 to 5` |
| 6 | otherwise | 200 | updated task |

The single write, `task["priority"] = ...`, is the last statement before `return`, after every
check, so a rejected request cannot partially modify `TASKS`.

## 2. `routes/api.py`: new PATCH route

Add `update_task_priority` to the existing `services.tasks` import, and add after
`get_task_route`:

```python
@api.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_route(task_id):
    return jsonify(update_task_priority(task_id, request.get_json()))
```

- Success returns 200 with the full task (`id`, `title`, `done`, `user_id`, `priority`).
- Errors flow through the existing `@api.errorhandler(AppError)`; it is not modified.
- The `/api` prefix comes from the blueprint registration in `app.py`, which is not touched.
- Existing GET and POST routes are not edited.

## 3. `tests/test_tasks.py`: 35 new cases (31 -> 66)

No existing test covers updating a task, so new tests are needed. No existing test or fixture is
modified; the only edit to existing lines is adding `update_task_priority` to the
`services.tasks` import. Every new test requests `restore_tasks`, including the ones that expect
rejection. New tests target task 2 and build expected values from a deep copy taken inside the
test (see "Mutation risks").

Service level (19 cases):
- `test_update_task_priority_valid`, parametrized `[1, 5]`: returns the stored record
  (`result is TASKS[2]`), priority updated, all other fields of task 2 equal to the snapshot,
  tasks 1 and 3 equal to the snapshot.
- `test_update_task_priority_invalid_priority`, parametrized
  `[True, False, "3", 3.0, 2.5, 0, 6, -1, None]`: `ValidationError`, status 422, message
  `Invalid priority: must be an integer from 1 to 5`, `TASKS == deep copy`.
- `test_update_task_priority_invalid_updates`, parametrized over (payload, message):
  `{}`, `{"title": "x"}`, `{"priority": 2, "title": "x"}`, `{"priority": 2, "done": True}`,
  `[]`, `None`: `ValidationError`, status 422, the message from the table, `TASKS == deep copy`.
- `test_update_task_priority_not_found`, parametrized `[{"priority": 2}, {"priority": 9}]` with
  task ID 999: `NotFoundError`, status 404, `Task not found`, `TASKS == deep copy`. The second
  case pins the 404-before-422 order.

API level (16 cases), using the existing `client` fixture:
- `test_api_update_task_priority`, parametrized `[1, 5]`: `PATCH /api/tasks/2` returns 200, the
  JSON equals the snapshot of task 2 with the new priority, `TASKS[2]["priority"]` is updated,
  and a following `GET /api/tasks/2` returns the same body.
- `test_api_update_task_invalid_priority`, parametrized
  `[None, True, False, "3", 3.0, 2.5, 0, 6, -1]`: 422, exact error body, `TASKS == deep copy`.
- `test_api_update_task_invalid_body`, parametrized over (body, message): `{}`,
  `{"title": "x"}`, `{"priority": 2, "title": "x"}`, `[]`: 422, exact error body,
  `TASKS == deep copy`.
- `test_api_update_task_not_found`: `PATCH /api/tasks/999` with `{"priority": 2}` returns 404
  with `{"error": "Task not found"}`, `TASKS == deep copy`.

## Edge cases, mutation risks, compatibility

Assumptions (the requirements do not fix these; say so if you want them changed):
1. **404 beats 422.** An unknown task ID with an invalid body returns 404, because the resource
   is resolved before the body is examined. Either order leaves `TASKS` unchanged.
2. **Error wording.** Messages for cases 2 to 4 in the table are new text built with the existing
   `ValidationError(field, reason)`. Case 5 reuses the existing message unchanged.
3. **Unsupported field plus valid priority is rejected entirely** (`{"priority": 2, "title":
   "x"}` -> 422, priority not applied), per requirements 5 and 6.
4. **Malformed JSON or a non-JSON Content-Type is out of scope.** `request.get_json()` keeps
   Flask's default 400/415 for those, the same as the existing POST route. No test covers it.
   A literal JSON `null` body does reach the service and returns 422 (case 2).

Mutation risks:
- `update_task_priority` returns the live `TASKS` record, the same as `get_task` and
  `create_task`. Returning a copy would be a new convention, so it is not introduced.
- `test_process_order_valid` (existing, unchanged) sets `TASKS[1]["done"] = True` without
  restoring it, so task 1 is not in its seed state for later tests. New tests therefore use
  task 2 and compare against an in-test snapshot rather than hard-coded seed values.
- Updating to the value the task already has is a normal 200; no special case.

Compatibility:
- `GET /api/tasks/<id>` and `POST /api/tasks` are untouched; PATCH is a new method on an existing
  URL rule, so previously PATCH returned 405 and now returns 200/404/422.
- Non-integer or negative IDs (`/api/tasks/abc`, `/api/tasks/-1`) do not match `<int:task_id>`
  and keep Flask's routing 404, as for GET.
- No new Ruff findings expected: the new import is used and Ruff has reported no line-length
  finding in earlier sessions. Existing findings may shift line numbers in
  `tests/test_tasks.py` only if lines are added above them; the import edit will be kept on one
  logical statement so they should not move.

## Verification

1. `.venv/Scripts/python -m pytest -q`: expect 66 passed (31 existing + 35 new).
2. `.venv/Scripts/python -m ruff check .`: expect the same 5 findings, no new ones.
3. `git diff --stat`: expect only `services/tasks.py`, `routes/api.py`, `tests/test_tasks.py`.
4. `git diff` review: existing tests, `_validate_priority`, `create_task`, the error handler and
   the GET/POST routes show no changes.
5. Report any difference between this plan (or its amended version) and the implementation,
   without inventing any.
