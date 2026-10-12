# Plan Log

## Supervision Log

| Session # | Prompt summary (≤15 words) | Did you amend the plan? | What you changed | Did output match amended plan? |
|---|---|---|---|---|
| 1 | Plan service-layer task priority (1–5, default 3) with validation and tests. | Yes | Required a `restore_tasks` fixture that snapshots `TASKS` and restores it in `finally`, used by every new test that mutates `TASKS`. Also required results that do not depend on execution order and an expected test count checked against the parametrized cases; the amended plan answered with a count of 16 and a reverse-order run. The original plan relied only on new tests not asserting fixed task IDs. | Yes |
| 2 | Plan optional priority support in POST /api/tasks, reusing service validation, with API tests. | No | No amendment. The original plan was saved before approval, displayed in full for review (route code, API tests, error handling, verification steps), and approved to be followed exactly, with the distinction between an omitted `priority` and an explicit `null` called out. The plan already met each requirement in the prompt: the route checks whether the `priority` key is present, so `null` reaches the service and gets 422; validation is reused from `services/tasks.py` with no new route logic; the tests cover omitted, 1 to 5 and nine invalid values (`null`, `true`, `false`, `"3"`, `2.5`, `3.0`, `0`, `6`, `-1`), with `TASKS` restored after every test. Result: 31 passed (15 new), Ruff unchanged at 5. | Yes |
| 3 | Plan PATCH `/api/tasks/<id>` priority updates with validation, 404 handling and data-integrity tests. | Yes | Amendment: the original plan called `data.get("priority")` on any body, so a missing key was treated like `null` (422 with the generic priority message) and non-object JSON bodies were left unhandled. Feedback sent into the Plan Mode session: a missing key returns its own 422, `Invalid priority: is required`, and a non-object body returns 422 before the task lookup (decisions 3 and 4 unchanged). Mismatch 1, test run versus executed plan: the first run was 1 failed, 72 passed. `test_update_task_non_object_body[None]` got 415, not 422, because the Flask test client sends no body for `json=None`; the executed plan had listed the bodies as Python values. Only the test inputs changed, to literal JSON strings sent with `data=` and a JSON content type, and the rerun gave 73 passed; the route was not touched. Mismatch 2, saved plan versus executed plan: `plans/session3-amended-plan.md` is a reconstruction written from a revision drafted in a separate conversation outside Plan Mode, and it was never executed. The Plan Mode session (transcript `60d49598`) revised its own plan, preserved as `plans/session3-executed-plan.md`, and implemented that. Its 13 new tests match the executed plan by name but differ from the saved plan in four ways: the null and array tests were combined into one renamed test, the empty-object test kept its original name and gained a case, an unplanned ignored-fields test was added, and the non-object-before-lookup test was renamed. The two plans agree on the production design, and the production code matched it. | Partially |
| 4 | Plan optional ?priority= filter on GET /api/tasks with isolated service and API tests. | No | No amendment. While planning, Claude asked two questions and the reviewer chose: add an unfiltered `GET /api/tasks` (none existed, it returned 405), and reject a repeated `priority` parameter with 422 even when the values are identical. The plan was then approved as written. Divergence: the production code matched, but the tests have five additions beyond the plan and nothing missing: a third query (`user_id=1`) in the ignore-other-params test; `[1, 2, 3]` id-order assertions in the unfiltered service and API tests; `TASKS == snapshot` and full-response-body assertions in the API filter tests; a check that every returned task has the requested priority; and two filtered calls, not one, in the no-mutation test. The additions make the tests stricter about result order, unchanged `TASKS` and exact bodies, and none changes behavior. Why: not recorded. The implementing session's summary (transcript `67b67774`) said the filter was implemented as planned and did not mention the additions. | Partially |

Sessions 1 and 3 were amended. Sessions 3 and 4 are marked Partially because of test-level differences only; in both, the production code matched the approved plan. The detailed evidence for each row is in the session entries below. Clarifications found in a later audit, including a mapping from the commit IDs cited here to the IDs on GitHub, are collected under "Audit notes" at the end of this file.

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

## PA 5, Task 1 — Session 2: Priority support in `POST /api/tasks`

- **Date:** 2026-10-11
- **Scope:** `routes/api.py` and the API tests only. `services/tasks.py` is not modified.
- **Base commit:** `309a4ef` (PA5 Task 1 Session 1: add task priority service layer)
- **Saved plan:** `plans/session2-original-plan.md`

### Original plan

Saved as `plans/session2-original-plan.md`. It proposed:

- `create_task_route` forwards an optional `priority` from the JSON body to `create_task`, reusing the validation and default added in Session 1. No validation is added to the route.
- The route checks whether the `priority` key is present rather than using `data.get("priority")`, so an explicit `null` reaches the service and is rejected instead of being treated as omitted.
- When `priority` is omitted, the route calls `create_task` without it and the service default of 3 applies. The route does not import or repeat `DEFAULT_PRIORITY`.
- Invalid values are rejected by the existing `ValidationError`, which the existing `@api.errorhandler(AppError)` turns into HTTP 422. The handler and status mapping are unchanged.
- The response is the stored task, which already includes `priority`.
- A new `tests/test_api.py` with its own `client` fixture and a local `TASKS` snapshot/restore fixture applied to every test, holding three tests (15 collected cases): priority omitted, valid priorities 1 to 5, and nine invalid values (`null`, `true`, `false`, `"3"`, `2.5`, `3.0`, `0`, `6`, `-1`).
- Behavior for a missing `title` or `user_id`, or a non-object body, is left as it was.

### Plan review

Approved without amendment. The plan was saved to `plans/session2-original-plan.md` before review, and no amended plan was produced.

### Implementation

Two implementation files were changed:

| File | Change |
|---|---|
| `routes/api.py` | `create_task_route` passes `data["priority"]` to `create_task` when the key is present, and otherwise calls it with two arguments. 5 insertions, 1 deletion. Imports are unchanged. |
| `tests/test_api.py` | New file: the `client` fixture, an autouse `restore_tasks` fixture using the same deep-copy and `try/finally` restore as `tests/test_tasks.py`, and the three planned tests. |

No other implementation file was changed, including `services/tasks.py`, `services/users.py`, `utils/errors.py`, `app.py`, `tests/test_tasks.py`, `requirements.txt` and `CLAUDE.md`.

### Verification

| Check | Command | Result |
|---|---|---|
| Baseline before implementation | `python -m pytest -v -p no:cacheprovider`, `python -m ruff check . --no-cache` | 16 passed; 5 Ruff findings |
| Full suite | `python -m pytest -v -p no:cacheprovider` | 31 passed: 16 existing + 15 new API cases |
| Lint | `python -m ruff check . --no-cache` | 5 findings, none new |

The 15 new cases are 1 omitted-priority case (201, priority 3 returned and stored), 5 valid-priority cases (201, value returned and stored) and 9 invalid-priority cases (422, the existing error message, nothing stored).

The 5 Ruff findings are the same pre-existing ones listed under Session 1 and were left in place, as `CLAUDE.md` requires. `routes/api.py` and `tests/test_api.py` introduce none.

### Plan divergence

None observed. The route body matches the code in `plans/session2-original-plan.md`, and the test names, parameter lists and assertions match the plan's test table.

### Outcome

The approved plan was implemented successfully. Session 3 has not been started.

## PA 5, Task 1 — Session 3: `PATCH /api/tasks/<id>` priority updates

- **Date:** 2026-10-11
- **Scope:** `services/tasks.py`, `routes/api.py`, `tests/test_tasks.py` and `tests/test_api.py`.
- **Base commit:** `37990e1` (PA5 Task 1 Session 2: support priority in POST API)
- **Saved plans:** `plans/session3-original-plan.md`, `plans/session3-amended-plan.md`

### Original plan

Saved as `plans/session3-original-plan.md`, a byte-for-byte copy of the Plan Mode plan file. It proposed:

- A service-layer `update_task_priority(task_id, priority)` in `services/tasks.py` that looks the task up with `get_task()`, validates the priority, then assigns it, so the route never touches `TASKS` directly.
- A shared private helper `_validate_priority()` holding the priority rule, called by both `create_task()` and `update_task_priority()`, with `create_task()`'s behavior, signature and docstring unchanged.
- A `PATCH /api/tasks/<id>` route in `routes/api.py` that passes `data.get("priority")` to the service and returns 200 with the updated task. Errors go through the existing `@api.errorhandler(AppError)`: 404 for an unknown task, 422 for an invalid priority, with the lookup first.
- New service tests in `tests/test_tasks.py` and API tests in `tests/test_api.py`, each rejection test asserting `TASKS` is unchanged.

The original plan treated a body without a `priority` key like `null`, and left non-object JSON bodies unhandled as out of scope.

### Amendment requested

The plan was not approved as written. The reviewer pointed out that the proposed route calls `data.get("priority")` without checking that the JSON body is an object, so JSON `null`, arrays and other non-object bodies could raise an unhandled exception.

Requested changes:

- Handle a missing `priority` and non-object JSON bodies explicitly, with a controlled HTTP 422 response that uses the existing error-handling conventions.
- Keep valid updates, invalid-value validation and missing-task behavior unchanged.
- Preserve the service-layer architecture and existing file boundaries.
- Add API tests for an empty JSON object, JSON `null` and a JSON array, and ensure rejected requests do not mutate `TASKS`.

### Approved plan

Saved as `plans/session3-amended-plan.md`. The revision was presented in the conversation outside Plan Mode, so this file was written from that text rather than copied from a Plan Mode plan file. The service-layer design is the same as in the original plan. The route design adds two checks before the service call, both raising the existing `ValidationError`:

- A body that is not a JSON object returns 422 `Invalid request body: must be a JSON object`.
- A body without a `priority` key returns 422 `Invalid priority: is required`.

Approved decisions:

- A missing `priority` gets its own message, `Invalid priority: is required`, rather than reusing the invalid-value message.
- Body-shape checks run in the route before the task lookup, so a non-object body returns 422 even for an unknown task ID.
- The resulting order is: body is an object (422), `priority` key present (422), task exists (404), priority value valid (422), then assign.
- Other keys in the body are ignored. Malformed JSON and a missing JSON content type stay out of scope.

### Implementation

Four implementation files were changed:

| File | Change |
|---|---|
| `services/tasks.py` | Added `_validate_priority()` and `update_task_priority()`; `create_task()` calls the helper instead of its inline check. 33 insertions, 3 deletions. |
| `routes/api.py` | Imported `update_task_priority` and `ValidationError`; added `update_task_route` for `PATCH /tasks/<int:task_id>` with the two body checks. 11 insertions, 2 deletions. |
| `tests/test_tasks.py` | Extended the import; added 4 test functions (16 collected cases). Existing tests are unchanged. |
| `tests/test_api.py` | Added 9 test functions (26 collected cases). Existing tests are unchanged. |

`git diff --stat`: 4 files changed, 150 insertions, 6 deletions. The 42 new test cases are 16 service cases and 26 API cases.

No other implementation file was changed, including `utils/errors.py`, the `AppError` handler, `app.py`, `services/users.py`, `requirements.txt` and `CLAUDE.md`.

### Verification

| Check | Command | Result |
|---|---|---|
| Baseline at `37990e1` | `pytest -q`, `ruff check .` on an export of the base commit | 31 passed; 5 Ruff findings |
| Full suite | `.venv/Scripts/python -m pytest -q` | 73 passed: 31 existing + 42 new |
| Lint | `.venv/Scripts/python -m ruff check .` | 5 findings, none new |

The 5 Ruff findings are the same pre-existing ones listed under Session 1, at the same locations, and were left in place, as `CLAUDE.md` requires.

### Plan divergence

The production code in `services/tasks.py` and `routes/api.py` matches `plans/session3-amended-plan.md`. The divergences are confined to how the API tests in `tests/test_api.py` are named and grouped; none changes behavior:

1. The planned `test_update_task_json_null` and `test_update_task_json_array` were combined into one `test_update_task_non_object_body`, parametrized over `[]`, `[1]`, `"3"`, `3` and `null`. The planned array inputs were `[]` and `[{"priority": 2}]`.
2. The empty-object test kept its original name, `test_update_task_missing_priority`, instead of the planned `test_update_task_empty_object`, and gained a second missing-key case, `{"title": "No priority"}`.
3. `test_update_task_ignores_other_fields` was added although it was not in the plan. It pins the decision that other body keys are ignored.
4. The planned `test_update_task_not_found_with_non_object_body` was named `test_update_task_non_object_body_checked_before_lookup`, with the same assertions.

Minor coverage gap: an unknown task ID with an empty JSON object (`{}`) is not directly tested. The route handles it, because the missing-key check runs before the service call; only the unknown-task case with `[]` is pinned by a test.

### Outcome

The amended behavior was implemented successfully; see the correction below for which plan was executed. Session 4 has not been started.

### Correction added 2026-10-12: saved plan versus executed plan

A later review of the Session 3 transcripts found that this entry uses "the amended plan" for two different documents.

- **Saved reconstructed plan:** `plans/session3-amended-plan.md`. It was written in a separate conversation, outside Plan Mode, from a revision drafted there. Its "Decisions to confirm" list is what the approval of decisions 1 and 2 refers to. It was not executed verbatim.
- **Executed plan:** the Plan Mode session that implemented Session 3 (transcript `60d49598`) did not read the saved file. After receiving the approval of decisions 1 and 2 it revised its own Plan Mode plan and implemented that. The executed plan is preserved as `plans/session3-executed-plan.md`, a byte-for-byte copy (10,084 bytes, SHA-256 `5afe4abcd97cb9c92234d89e37e1c78af9c87c103ba1149b59d80b60c9a41cf6`) of that session's Plan Mode file, `pasted-content-id-03f1-pa5-task-ethereal-crescent.md`. The transcript shows the session last edited that file at 03:47:30 UTC, before the plan was approved at 03:47:42 and before the first implementation edit at 03:47:53, and the file has not changed since. One caveat: the plan text recorded with the approval call differs from the file in the API test list, where it has one line for the missing-priority test and the file has four lines; that last edit to the file was made in the same step as the approval request. The implemented tests follow the file.
- **Where they agree:** the two approved decisions, the service-layer design and the PATCH route code. This is why the production code matches the saved plan.
- **Where they differ:** the API test list. The four differences under "Plan divergence" are differences between the saved plan and the executed plan, and the implementation follows the executed plan's test names and cases.
- **Test runs:** the first run after implementation was 1 failed, 72 passed. `test_update_task_non_object_body[None]` got 415, not 422, because the Flask test client sends no body for `json=None`. The executed plan had listed the non-object bodies as Python values; the test was changed to send literal JSON strings, and the rerun gave 73 passed. The Verification table above records only the final result.

The "Approved plan" heading and the comparison under "Plan divergence" should be read with this correction: they describe the saved reconstructed plan. The original saved plan files are unchanged; `plans/session3-executed-plan.md` was added on 2026-10-12 alongside them.

## PA 5, Task 1 — Session 4: Optional `?priority=` filter on `GET /api/tasks`

- **Date:** 2026-10-11 (audited and committed 2026-10-12)
- **Scope:** `services/tasks.py`, `routes/api.py`, `tests/test_tasks.py` and `tests/test_api.py`.
- **Base commit:** `1420231` (PA5 Task 1 Session 3: add PATCH priority updates)
- **Saved plan:** `plans/session4-original-plan.md`

### Planning discovery and decisions

Inspection during planning found that `GET /api/tasks` did not exist: `/api/tasks` accepted only POST, so GET returned 405, and there was no list-all service function. Two decisions were made by the reviewer before the plan was written:

- Add an unfiltered listing endpoint: `GET /api/tasks` without `priority` returns all tasks.
- Reject a repeated `priority` query parameter with HTTP 422, even when the values are identical.

### Original plan

Saved as `plans/session4-original-plan.md`, a byte-for-byte copy of the Plan Mode plan file, before implementation. It proposed:

- A service-layer `list_tasks(priority=None)` in `services/tasks.py` that returns a new list of all tasks, or validates the priority with the existing `_validate_priority()` and returns the matching tasks. It never assigns into `TASKS`.
- A shared `PRIORITY_REASON` constant holding the existing message text, used by `_validate_priority()` and by the route, so the string is not copied.
- A `GET /tasks` route in `routes/api.py` that checks for a repeated parameter, parses the value as a plain ASCII decimal integer, then calls the service. Errors are raised as the existing `ValidationError` and converted by the existing `@api.errorhandler(AppError)`.
- Isolated service tests in `tests/test_tasks.py` using the existing `restore_tasks` fixture, and API tests in `tests/test_api.py` under its autouse `restore_tasks` fixture.

### Plan review

Approved without amendment. No amended plan was produced.

### Approved behavior

| Request | Response |
|---|---|
| `GET /api/tasks` | 200, every task in `TASKS` order |
| `?priority=N` for N from 1 to 5 | 200, the tasks with that priority |
| Valid priority, no matches | 200, `[]` |
| Value that is not a plain decimal integer (including empty), or out of range | 422 `Invalid priority: must be an integer from 1 to 5` |
| `priority` given more than once | 422 `Invalid priority: must be provided at most once` |
| Leading zeros (`?priority=03`) | Accepted as 3 |
| Other query parameters | Ignored |

### Implementation

Four implementation files were changed:

| File | Change |
|---|---|
| `services/tasks.py` | Added `PRIORITY_REASON`; `_validate_priority()` uses it in place of the literal, with the same text; added `list_tasks()` after `get_tasks_for_user`. 21 insertions, 1 deletion. |
| `routes/api.py` | Imported `list_tasks` and `PRIORITY_REASON`; added `list_tasks_route` for `GET /tasks`. 17 insertions, 1 deletion. |
| `tests/test_tasks.py` | Extended the import; added 4 test functions (15 collected cases). Existing tests are unchanged. |
| `tests/test_api.py` | Added 7 test functions (31 collected cases). Existing tests are unchanged. |

`git diff --stat`: 4 files changed, 138 insertions, 3 deletions.

No other implementation file was changed, including `utils/errors.py`, the `AppError` handler, `app.py`, `services/users.py`, `requirements.txt` and `CLAUDE.md`. The POST, PATCH and GET-by-ID routes are not in the diff.

### Verification

| Check | Command | Result |
|---|---|---|
| Baseline before implementation | recorded in the plan | 73 passed; 5 Ruff findings |
| Full suite | `.venv/Scripts/python -m pytest -q` | 119 passed: 73 existing + 46 new |
| Lint | `.venv/Scripts/python -m ruff check .` | 5 findings, none new |

The 46 new cases are 15 service cases and 31 API cases. The 5 Ruff findings are the same pre-existing ones listed under Session 1, at the same locations, and were left in place, as `CLAUDE.md` requires.

### Plan divergence

The production code in `services/tasks.py` and `routes/api.py` matches `plans/session4-original-plan.md`. The differences are confined to the tests, and all are additions; no planned test or case is missing or renamed:

1. `test_list_tasks_ignores_other_params` in `tests/test_api.py` adds a third query, `user_id=1`, to the two planned ones, and its setup first sets task 1 to priority 1.
2. Both `test_list_tasks_without_priority` tests also assert that the task ids are `[1, 2, 3]`, pinning the order.
3. The API `test_list_tasks_with_priority` and `test_list_tasks_no_matches` also assert `TASKS == snapshot`, and the former compares full response bodies where the plan said expected ids.
4. The service `test_list_tasks_with_priority` also asserts that every returned task has the requested priority.
5. `test_list_tasks_does_not_modify_tasks` clears the results of two filtered calls (priorities 3 and 1) rather than one.

Coverage gaps:

- `?priority=03` has no automated test. It was checked manually during the audit with an in-memory request and returned 200 with the priority-3 tasks.
- A valid `priority` combined with an unrelated parameter (`?priority=003&done=true`) also has no automated test; the same manual check returned 200 with the priority-3 tasks.
- HEAD/OPTIONS and trailing-slash behavior, listed in the plan's edge cases, were not verified in the audit.

### Outcome

The approved plan was implemented successfully. Task 2 has not been started.

## Audit notes

Added 2026-10-12, after a read-only audit of the published repository against the session transcripts. These notes clarify the entries above. Nothing above was rewritten, and the saved plans in `plans/` were not changed.

### Commit IDs

The session entries cite the original local commit IDs. The same commits were later published on GitHub on top of an earlier history, which gave them new IDs:

| Cited as | Published as | Commit |
|---|---|---|
| `eeaf95f` | `442e121` | Week 4 starter: task-manager before PA 5 |
| `309a4ef` | `836cbcd` | PA5 Task 1 Session 1: add task priority service layer |
| `37990e1` | `f5f0939` | PA5 Task 1 Session 2: support priority in POST API |
| `1420231` | `f9f37fe` | PA5 Task 1 Session 3: add PATCH priority updates |
| `b089889` | `0e47292` | PA5 Task 1 Session 4: add priority filtering |
| `fdf93c5` | `f767d7a` | PA5 Task 2: document subagent decomposition |

`plans/session2-original-plan.md` and `plans/session4-original-plan.md` also cite local IDs. They are saved evidence and were left as written.

### Session 1: how implementation was approved

The amendment was typed inside the Plan Mode session, and the revised plan was approved by a typed message, after which implementation started. Unlike Sessions 2 to 4, the Session 1 transcript has no recorded Plan Mode exit before the first implementation edit. The "Yes" for the amendment in the table is not affected.

### Session 3: what was sent into the Plan Mode session

The only amendment text sent into the Plan Mode session was the approval of two decisions: a missing `priority` returns 422 with "Invalid priority: is required", and non-object JSON bodies return 422 before the task lookup. Decisions 3 and 4 were left unchanged. The extra API tests for `{}`, JSON `null` and a JSON array that are listed in this session's table row were drafted in the separate conversation described in the correction above, not typed into the Plan Mode session.

### Session 4: working directory

The Session 4 Plan Mode session started in the user's home folder, not in the repository, so the project's `CLAUDE.md` was not loaded automatically. The session read `CLAUDE.md` and the code by absolute path before planning, and all of the changes it made are in this repository.
