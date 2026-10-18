# Use this right after a scoped change to confirm that only the intended files changed and that tests and lint still match the baseline; do not use it to make or fix changes, or while a change is still in progress.

## Goal
Check a finished change against its scope. `$ARGUMENTS` is the list of files the change was allowed to touch, separated by spaces, for example `services/tasks.py tests/test_tasks.py`. Report whether the working tree changed only those files and whether the tests and lint are still at baseline.

If `$ARGUMENTS` is empty, stop and ask for the allowed files. Do not guess.

## Context
- This is the check that ended every PA 5 session in this project (see `PLAN_LOG.md`): run the tests, run Ruff, and compare `git diff --stat` with the files the task allowed.
- Commands from `CLAUDE.md`: `.venv/Scripts/python -m pytest -q` and `.venv/Scripts/python -m ruff check .`. The Ruff baseline is the 5 pre-existing findings that `CLAUDE.md` says not to fix, and two of them are in `routes/api.py`, so touching a file that has a baseline finding is not a regression by itself. Compare findings by file and rule code, not by line number, because line numbers move. The baseline is: `app.py` I001, `routes/api.py` I001, `routes/api.py` F401, `tests/test_tasks.py` I001, `tests/test_tasks.py` B017. A regression is a count above 5 or any finding whose file and rule code are not in that list.
- `utils/errors.py` and `requirements.txt` are protected by the hook in `.claude/hooks/guard_writes.py`. If either one shows up as changed, report it as out of scope even if it is listed in `$ARGUMENTS`.

## Constraints
- Read-only. Do not edit, stage, commit, revert or reformat anything, and do not fix what you find. Report it.
- Run only `git status --short`, `git diff --stat`, the pytest command and the Ruff command.
- Judge by the output of those commands, not by what the change was meant to do. Untracked files count as changes.

## Verification
- Give a table with each changed or untracked file and whether it is in scope or out of scope, and list any file named in `$ARGUMENTS` that did not change.
- Give the exact `pytest -q` result line and the Ruff finding count compared with the baseline of 5. List every Ruff finding as file and rule code, and mark each one as in the baseline or new.
- End with one verdict line, IN SCOPE or OUT OF SCOPE, and the reason. The verdict is OUT OF SCOPE only if a changed file is not in `$ARGUMENTS`, a protected file changed, `pytest -q` is not green, or there is a Ruff regression as defined above. Baseline findings alone never make it OUT OF SCOPE.
