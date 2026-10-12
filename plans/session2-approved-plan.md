# PA 5 Task 1 — Session 2: expose task priority through POST /api/tasks

## Context

Session 1 added priority to the service layer: `create_task(title, user_id, priority=DEFAULT_PRIORITY)`
in `services/tasks.py` validates with `_validate_priority` and raises
`ValidationError("priority", "must be an integer from 1 to 5")` (HTTP 422). The route
`create_task_route` in `routes/api.py` still calls `create_task(data["title"], data["user_id"])`,
so an API client cannot set a priority, and a `priority` key in the body is silently ignored.
Session 2 passes the field through the route and adds API-level tests. No service change is needed.

## Pre-planning findings (read-only)

- `PLAN_LOG.md` references both `plans/session1-original-plan.md` and
  `plans/session1-amended-plan.md`. Both files exist; sizes (5,436 / 6,135 bytes) and SHA-256
  hashes match the values recorded in the log. No missing references.
- Git state: `M services/tasks.py`, `M tests/test_tasks.py` (Session 1 work, uncommitted),
  `?? PLAN_LOG.md`, `?? plans/`. `git diff --stat`: 2 files, 70 insertions, 8 deletions. Nothing modified by this session.
- Baseline measured now: `pytest` 19 passed; `ruff check .` 5 findings
  (`app.py` I001; `routes/api.py` I001 and F401 `process_order`; `tests/test_tasks.py` I001 and B017).
  CLAUDE.md's "4 tests / 6 findings" is out of date; the measured baseline is used below.
- `routes/api.py` already has `@api.errorhandler(AppError)` returning `{"error": e.message}` with
  `e.status_code`; `app.py` registers the blueprint under `/api`. Both stay untouched.
- There are no existing API-level tests and no Flask test client fixture. `tests/test_tasks.py`
  has the `restore_tasks` fixture (deep-copy snapshot, restore in `finally`), which is reused.

## Change 1 — `routes/api.py` (`create_task_route` only)

Current:

```python
    data = request.get_json()
    return jsonify(create_task(data["title"], data["user_id"])), 201
```

Proposed:

```python
    data = request.get_json()
    if "priority" in data:
        return jsonify(create_task(data["title"], data["user_id"], data["priority"])), 201
    return jsonify(create_task(data["title"], data["user_id"])), 201
```

- Key presence, not `data.get(...)`, decides the branch, so an explicit `"priority": null` reaches
  the service as `None` and is rejected, while an omitted key uses the service default of 3.
- The route does not validate or hold the default; `_validate_priority` and `DEFAULT_PRIORITY`
  stay the single source in `services/tasks.py`. The existing error handler turns the
  `ValidationError` into the 422 response.
- The import line is not edited (no new names needed), so the two existing Ruff findings in this
  file stay exactly as they are.

## Change 2 — `tests/test_tasks.py`

The 19 existing tests and the `restore_tasks` fixture are not edited. Additions:

1. Import `from app import app` in the existing import block.
2. Fixture:
   ```python
   @pytest.fixture
   def client():
       return app.test_client()
   ```
3. Three tests, each requesting `restore_tasks` and `client`, posting with
   `client.post("/api/tasks", json=...)`:

| Test | Request body | Assertions |
|---|---|---|
| `test_api_create_task_without_priority` | `{"title": "Water plants", "user_id": 2}` | status 201; JSON equals `{"id": <max id + 1>, "title": "Water plants", "done": False, "user_id": 2, "priority": 3}`; `TASKS[<new id>]["priority"] == 3` |
| `test_api_create_task_with_priority`, parametrized `[1, 5]` | same plus `"priority": <value>` | status 201; response `priority` equals the value sent |
| `test_api_create_task_invalid_priority`, parametrized `[None, True, False, "3", 3.0, 2.5, 0, 6, -1]` | same plus `"priority": <value>` | status 422; JSON equals `{"error": "Invalid priority: must be an integer from 1 to 5"}`; `TASKS` equals a deep copy taken before the request |

   The invalid-priority test compares the whole `TASKS` dictionary, not only its keys, which is the
   stricter check PLAN_LOG.md listed as a coverage opportunity.

New test cases: 1 + 2 + 9 = 12.

## Risks

- `3.0` must stay a float through JSON. Flask's test client serializes it as `3.0` and
  `request.get_json()` parses it back as `float`, so the service rejects it. The parametrized case verifies this.
- `from app import app` is a new import in the tests. It works because pytest is run from the
  repository root, the same way `services` is already imported.
- The import block in `tests/test_tasks.py` already has an I001 finding; adding one import keeps
  it as one finding, not a new one. If Ruff reports anything else new, it will be fixed within the two allowed files and reported.
- Pre-existing behaviours left unchanged because they are outside this session's requirements:
  a body missing `title` or `user_id` raises `KeyError` (HTTP 500), a non-object JSON body is not
  handled, and `user_id` is not checked against `USERS`.
- Shared state: every new test uses `restore_tasks`, so created tasks do not leak into other tests.

## Verification after implementation

- `.venv/Scripts/python -m pytest -v` — expect 31 passed (19 existing + 12 new).
- `.venv/Scripts/python -m ruff check .` — expect the same 5 findings, none new.
- `git status --short` and `git diff --stat` — expect `routes/api.py` newly modified and
  `tests/test_tasks.py` further modified; `services/tasks.py` diff identical to its current diff;
  `app.py`, `utils/errors.py`, `services/users.py`, `CLAUDE.md`, `requirements.txt`, `PLAN_LOG.md`
  and `plans/` untouched (plan file hashes rechecked).
- Report actual results and any deviation from this plan.
