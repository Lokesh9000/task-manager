# Plan Log

## PA 5, Task 1 — Session 1: Service-layer task priority

- **Date:** 2026-10-11
- **Scope:** `services/tasks.py` and `tests/test_tasks.py` only. Routes are left for later sessions.
- **Base commit:** `eeaf95f` (Week 4 starter: task-manager before PA 5)
- **Saved plans:** `plans/session1-original-plan.md`, `plans/session1-amended-plan.md`

### Original plan

Saved as `plans/session1-original-plan.md`. It proposed:

- A `priority` field on tasks: an integer from 1 to 5 (1 = urgent, 5 = low).
- `create_task` gains a trailing `priority` parameter defaulting to 3, so existing two-argument callers keep working.
- All three seed tasks in `TASKS` get `"priority": 3`.
- Invalid priorities (out of range, non-integers, booleans, `None`) are rejected with `ValidationError`, before anything is stored.
- Four new tests (10 collected cases): seed priorities, default priority, explicit priority at both boundaries, and seven parametrized invalid values.

The original plan relied on new tests not asserting on fixed task IDs to stay independent of each other.

### Amendment requested

The plan was not approved as written. The reviewer pointed out that the new tests call `create_task()`, which mutates the shared module-level `TASKS` dictionary, and that avoiding fixed IDs does not stop that state leaking between tests.

Requested changes:

- Add a pytest fixture named `restore_tasks` that snapshots `TASKS` and restores it after each new test that creates or modifies tasks.
- Use `try/finally` so restoration also happens when a test fails.
- Apply the fixture to every new priority test that mutates `TASKS`.
- Leave existing tests unchanged and make results independent of execution order.
- Verify the expected test count from the actual number of parametrized cases.

### Approved plan

Saved as `plans/session1-amended-plan.md`. The service-layer design is the same as in the original plan. The test design adds:

- `restore_tasks`: takes a `copy.deepcopy` snapshot of `TASKS`, yields inside `try`, and in `finally` restores the dictionary in place with `clear()` and `update()`. It is not `autouse`.
- The fixture is used by the three tests that call `create_task` (default priority, explicit priority, invalid priority). The read-only seed test does not use it.
- An expected count of 16 collected tests: 6 existing + 3 single tests + 7 parametrized invalid-priority cases.
- Order checks as part of verification.

### Implementation

Only two files were modified:

| File | Change |
|---|---|
| `services/tasks.py` | Imported `ValidationError`; added `MIN_PRIORITY`, `MAX_PRIORITY`, `DEFAULT_PRIORITY`; added `"priority": 3` to the three seed tasks; extended `create_task` with the `priority` parameter, validation, stored field, and docstring `Args`/`Raises` entries. |
| `tests/test_tasks.py` | Extended the import block; added the `restore_tasks` fixture; added the four new priority tests. The six existing test functions are unchanged. |

`git diff --stat`: 2 files changed, 54 insertions, 8 deletions.

No other tracked file was changed, including `routes/api.py`, `services/users.py`, `utils/errors.py`, `requirements.txt` and `CLAUDE.md`.

### Verification

| Check | Command | Result |
|---|---|---|
| Baseline before implementation | `pytest -q`, `ruff check .` | 6 passed; 5 Ruff findings |
| Collection | `.venv/Scripts/python -m pytest --collect-only -q` | 16 tests collected |
| Full suite | `.venv/Scripts/python -m pytest -q` | 16 passed |
| New tests alone | `.venv/Scripts/python -m pytest -q -k priority` | 10 passed, 6 deselected |
| Reverse order | all 16 node IDs passed to pytest in reverse | 16 passed |
| Lint | `.venv/Scripts/python -m ruff check .` | 5 findings, none new |

The 5 Ruff findings are pre-existing and were left in place, as `CLAUDE.md` requires:

- `app.py:1` — I001 unsorted imports
- `routes/api.py:1` — I001 unsorted imports
- `routes/api.py:2` — F401 unused `process_order` import
- `tests/test_tasks.py:1` — I001 unsorted imports
- `tests/test_tasks.py:20` — B017 blind `pytest.raises(Exception)` (line 10 before this session; it moved because imports and the fixture were added above it)

### Plan divergence

None observed. The implementation was compared against each requirement in `plans/session1-amended-plan.md` and matches it.

### Outcome

The approved plan was implemented successfully. Session 1 was committed after verification. Session 2 has not been started.
