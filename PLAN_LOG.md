# Plan Log

COMP 4600/5300 PA 5, Task 1: Plan Mode sessions for the task-manager repository.

| Session # | Prompt summary (15 words maximum) | Did you amend the plan? Yes/No | What you changed | Did output match amended plan? Yes/Partially/No |
|---|---|---|---|---|
| 1 | Add task priority defaults, validation, and service-layer tests. | Yes | Required `test_seed_tasks_have_default_priority` and all new priority tests to use `restore_tasks`, ensuring shared-state isolation. | Yes |
| 2 | Expose task priority through POST endpoint and add API tests. | No | No amendment; approved the original plan without changes. | Yes |

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
