# Audit one service file for AppError handling; use it on a single file under services/, not to add features, fix lint or edit tests.

## Goal
Audit every function in the service file `$ARGUMENTS` (for example `services/tasks.py`) for missing or incorrect error handling, and fix only the functions that need it. A function needs a fix when it can raise a raw exception for an expected failure, such as a bare dictionary lookup that raises `KeyError` or a raised `Exception` or `ValueError`, instead of one of this project's `AppError` subclasses.

If `$ARGUMENTS` is empty or is not a file under `services/`, stop and ask which file to audit. Do not guess.

## Context
- The error classes live in `utils/errors.py`: `AppError(message, status_code=400)`, `NotFoundError(resource)` (404) and `ValidationError(field, reason)` (422). `routes/api.py` turns any `AppError` into a JSON `{"error": message}` response through `@api.errorhandler(AppError)`.
- `get_user()` in `services/users.py` is the canonical pattern: type hints, a Google-style docstring with `Args`, `Returns` and `Raises`, and `NotFoundError("User")` for a missing record.
- `CLAUDE.md` Conventions: use `NotFoundError` and `ValidationError` instead of raw `KeyError` or `Exception` for expected service errors, preserve public signatures, and check existing tests before changing them.
- Existing tests may assert on the exception type. Read the tests that cover a function before you change what it raises.

## Constraints
- If a function already uses AppError correctly, skip it. Do not rewrite it.
- Scope lock: edit only the file named in `$ARGUMENTS`. Never modify `utils/errors.py` (do not add error classes; use the existing ones), `routes/api.py`, or anything under `tests/`. If a test would need to change, stop and report it instead of editing the test.
- Change only what the error handling requires. Keep signatures, return values and behavior for valid input exactly as they are. If a function you change has no docstring, add a Google-style one with `Args`, `Returns` and `Raises` as `CLAUDE.md` requires. If it already has one, only add or update its `Raises` section. Leave the docstrings of skipped functions alone.
- Do not fix unrelated Ruff findings or reformat code.

## Verification
- Work one function at a time. After you change a function, run `.venv/Scripts/python -m pytest -q` before you look at the next function. If the suite is not green, fix or revert that function first. Do not wait until the end of the audit.
- When you finish, run `git diff --stat` and confirm that only the file named in `$ARGUMENTS` changed.
- Report the functions you changed (what each raised before and after), the functions you skipped and why, the `pytest -q` result line after each change, and the `git diff --stat` output.
