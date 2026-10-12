# Plan Log

COMP 4600/5300 PA 5, Task 1: Plan Mode sessions for the task-manager repository.

| Session # | Prompt summary (15 words maximum) | Did you amend the plan? Yes/No | What you changed | Did output match amended plan? Yes/Partially/No |
|---|---|---|---|---|
| 1 | Add task priority defaults, validation, and service-layer tests. | Yes | Required `test_seed_tasks_have_default_priority` and all new priority tests to use `restore_tasks`, ensuring shared-state isolation. | Yes |
| 2 | Expose task priority through POST endpoint and add API tests. | No | No amendment; approved the original plan without changes. | Yes |
| 3 | Implement PATCH task priority updates with validation and tests. | Yes | Added API-level JSON null request test to cover previously untested 422 behavior. | Yes |

## Session 1 evidence

### Plan artifacts

- Original plan: `plans/session1-original-plan.md` (5,436 bytes)
  - SHA-256: `98133ee34fe1aa59ff4392fa590b4984f8d2ffc571afd546aed8034911644fb9`
  - Provenance: extracted by script, unedited, from the plan-file write recorded before the
    amendment request in the Session 1 transcript
    `C:\Users\Lokes\.claude\projects\C--Users-Lokes-Downloads-task-manager-task-manager\71d3213b-b7f2-4d2e-bfe0-aa340faffaf3.jsonl`
- Amended plan: `plans/session1-amended-plan.md` (6,135 bytes)
  - SHA-256: `1e7702bce5ceb6dc5dc50c832033c1746f4a94f74d17736bc3add365a68215d8`
  - Provenance: byte-for-byte copy of the plan file
    `C:\Users\Lokes\.claude\plans\pasted-content-id-a7f1-we-are-flickering-candy.md`
- The plan file was edited in place when the amendment was applied, so it holds the amended plan
  only; the original exists outside this repository only in the transcript.
- Both hashes are of the files with LF line endings, as written. A checkout that converts line
  endings to CRLF will produce different hashes.
- Consistency check: applying the two plan edits recorded in the transcript to the original plan
  reproduces the amended plan exactly.

### Amendment

- Original plan: the `restore_tasks` fixture was "used only by the new tests that call
  `create_task`", so the read-only `test_seed_tasks_have_default_priority` did not use it.
- Amended plan: all four new priority tests request `restore_tasks`, including
  `test_seed_tasks_have_default_priority`, and the fixture restores `TASKS` in a `finally` block
  so it is restored even if a test fails. The six existing tests stay unchanged.
- Why: `TASKS` is a module-level dictionary shared by every test. The amendment makes all new
  priority tests use the same shared-state isolation mechanism instead of leaving one outside it.

### Files modified

- `services/tasks.py`
- `tests/test_tasks.py`

### Verification

- `.venv/Scripts/python -m pytest -q`: 19 passed (6 existing tests plus 13 new cases).
- `.venv/Scripts/python -m ruff check .`: 5 findings, the same 5 that existed before the session;
  no new findings.
- `git diff --stat`: only the two files above changed.

### Minor deviations observed

None of these changes the behaviour described in the amended plan.

1. `test_create_task_default_priority` contains an extra identity assertion
   (`TASKS[expected_id] is result`) that the plan did not list.
2. The existing B017 Ruff finding in `tests/test_tasks.py` moved from line 10 to line 20 because
   the fixture was added above it. It is the same finding on the same unedited test.
3. Some lines are long: the three seed rows in `services/tasks.py` are exactly 88 characters and
   the import line in `tests/test_tasks.py` is 90 characters. Ruff reports no line-length finding.

### Coverage improvement opportunity

`test_create_task_invalid_priority` checks that the set of `TASKS` keys is unchanged after a
rejected call, not that every record is unchanged. An independent one-off verification run outside
the test suite compared `TASKS` with a deep copy taken beforehand and confirmed full equality for
all nine invalid values.

## Session 2 evidence

### Plan artifact

- Approved plan: `plans/session2-approved-plan.md` (5,623 bytes)
  - SHA-256: `307f32240a0e0abbddfa94e8d0be547e931ebb51623e51bbd4af7bfc2eb88cda`
  - Provenance: byte-for-byte copy of the plan file
    `C:\Users\Lokes\.claude\plans\pasted-content-id-8b7a-comp-4600-5300-snoopy-wand.md`
- Transcript:
  `C:\Users\Lokes\.claude\projects\C--Users-Lokes-Downloads-task-manager-task-manager\cbb77919-f873-4562-aee7-2cea09c64870.jsonl`
- The plan was approved as first presented, so there is no separate amended plan. The plan file
  was written once and not edited afterwards.
- The hash is of the file with LF line endings, as written.

### Files modified

- `routes/api.py`
- `tests/test_tasks.py`

### Verification

- `.venv/Scripts/python -m pytest -q`: 31 passed (19 existing tests plus 12 new API cases).
- `.venv/Scripts/python -m ruff check .`: 5 findings, the same 5 that existed before the session;
  no new findings.
- Successful `POST /api/tasks` requests return 201, with priority 3 when `priority` is omitted or
  the supplied valid priority otherwise (1 and 5 are tested).
- Invalid priorities (null, true, false, `"3"`, 3.0, 2.5, 0, 6, -1) return 422 with the existing
  `ValidationError` response, and `TASKS` is unchanged, compared against a deep copy.

### Minor observations

None of these changes the behaviour described in the approved plan.

1. The existing B017 Ruff finding in `tests/test_tasks.py` moved from line 20 to line 25 because
   the import and fixture were added above it. It is the same finding on the same unedited test.
2. The plan did not specify placement: `from app import app` follows `import pytest`, and the
   `client` fixture follows `restore_tasks`.
3. Running pytest and Ruff refreshed `.pytest_cache` and `.ruff_cache`. Both are git-ignored.

## Session 3 evidence

### Plan artifacts

- Original plan: `plans/session3-original-plan.md` (8,731 bytes)
  - SHA-256: `bc30cc849473b596b028e8bcf24b595a613d304a5742695e6513cad6efc3a151`
  - Provenance: extracted by script, unedited, from the single plan-file write recorded before
    the amendment in the Session 3 transcript (line 45, tool call
    `toolu_01R9sgv5i6T3enCg7psfURpA`, 2026-10-12T00:23:07Z)
    `C:\Users\Lokes\.claude\projects\C--Users-Lokes-Downloads-task-manager-task-manager\53158e30-26b8-4a84-828b-a04701869f89.jsonl`
- Amended plan: `plans/session3-amended-plan.md` (9,492 bytes)
  - SHA-256: `2dccaf78ec0c7c983a29a13d787e2b2d2d42f08d778e421d50d372276aa9cf9d`
  - Provenance: byte-for-byte copy of the plan file
    `C:\Users\Lokes\.claude\plans\pasted-content-id-65f3-comp-4600-5300-curious-kettle.md`
- The plan file was edited in place when the amendment was applied, so it holds the amended plan
  only; the original exists outside this repository only in the transcript.
- Both hashes are of the files with LF line endings, as written. A checkout that converts line
  endings to CRLF will produce different hashes.
- Consistency check: applying the six plan edits recorded in the transcript (lines 71 to 81) to
  the original plan reproduces the amended plan exactly.

### Amendment

- Original plan: 35 new test cases, 66 total. It stated that a literal JSON `null` request body
  returns 422, but covered that only at the service level (`None`); at the API level,
  non-object JSON was tested only with `[]`.
- Amended plan: adds one API-level test, `test_api_update_task_null_body`, which sends the raw
  body `null` with `Content-Type: application/json` and expects 422 with
  `Invalid request: must be a JSON object` and `TASKS` unchanged. 36 new test cases, 67 total.
  No implementation code changed as a result of the amendment.
- Why: it was the only behaviour the plan asserted about Flask's body parsing that no test
  exercised. The gap was identified during plan review, before any source file was edited.

### Files modified

- `services/tasks.py`
- `routes/api.py`
- `tests/test_tasks.py`

### Verification

- `.venv/Scripts/python -m pytest -q`: 67 passed (31 existing tests plus 36 new cases).
- `.venv/Scripts/python -m ruff check .`: 5 findings, the same 5 that existed before the session
  (same rules, files and line numbers as at commit `246b401`); no new findings.
- `git diff --check`: no output.
- `git status --short`: only the three files above were modified by the implementation.
- Valid `PATCH /api/tasks/<id>` requests return 200 with the full task and only `priority`
  changed (1 and 5 are tested).
- Invalid requests (invalid priority values, missing priority, `{}`, unsupported fields,
  non-object JSON including `null`) return 422 through the existing `ValidationError`, and
  `TASKS` is unchanged, compared against a deep copy.
- Nonexistent task IDs return 404 through the existing `NotFoundError`, checked before the
  request body.

### Divergence from the amended plan

No genuine implementation divergence occurred. `update_task_priority` and the PATCH route match
the code in the amended plan, and all nine planned test functions are present with the planned
parameters (19 service-level and 17 API-level cases).
