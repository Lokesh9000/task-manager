# Task Manager

Python Flask API for managing tasks and users.

## Commands
- Install dependencies: `python -m pip install -r requirements.txt`.
- Run the full test suite with `python -m pytest -v`; the current baseline is 182 passing tests across `tests/test_tasks.py`, `tests/test_api.py`, and `tests/test_users.py`.
- After each subagent or scoped change, run `.venv/Scripts/python -m pytest -q` from the repository root and record the exact result line before moving on. This is the checkpoint `DECOMPOSITION.md` records after each subagent.
- Run lint with `python -m ruff check .`. The codebase has 5 pre-existing Ruff findings, so do not introduce new findings or perform unrelated lint cleanup.
- Slash commands live in `.claude/commands/`, and `COMMAND_LOG.md` records every real invocation:
  - `/project:audit-errors <file under services/>` audits each function in that one file for raw exceptions, changes only the ones that need `NotFoundError` or `ValidationError`, and runs `pytest -q` after each change. It skips functions that already use `AppError` correctly.
  - `/project:scaffold-endpoint <resource> <METHOD>` adds one endpoint to `routes/api.py` (this project's route module; there is no `routes/tasks.py`), with logic in `services/<resource>.py` and tests in `tests/test_api.py`. It asks instead of guessing when the arguments are wrong.
  - `/project:verify-scope <allowed files>` is a read-only check, run after a scoped change, that only the listed files changed and that `pytest -q` and Ruff still match the baseline.

## Architecture
- Keep the request flow layered as `routes/api.py` → `services/*.py` → the module-level data stores such as `TASKS` and `USERS`.
- Route functions in `routes/api.py` should handle HTTP concerns and call service functions rather than duplicating task or user logic.
- For user notification preferences, `routes/api.py` only checks the request shape and delegates listing, reading, and updating to `list_users()`, `get_notification_pref()`, and `set_notification_pref()` in `services/users.py`, which owns `USERS`, the allowed values, validation, and errors.
- Use `services/users.py` as the canonical example for service-layer structure, validation, type hints, docstrings, and application errors.
- Application errors belong in `utils/errors.py`; `routes/api.py` already converts `AppError` instances into HTTP responses.

## Conventions
- All service functions in `services/tasks.py` and `services/users.py` must use parameter and return type hints, following `get_user()` in `services/users.py`.
- Service functions must use Google-style docstrings with `Args`, `Returns`, and `Raises` sections when applicable, following `services/users.py`.
- Use `NotFoundError` and `ValidationError` from `utils/errors.py` instead of raw `KeyError` or generic `Exception` for expected service errors.
- Preserve existing public function signatures unless the task explicitly requires a change.
- When a requested service behavior is ambiguous and existing code or tests do not establish the expected behavior, do not invent additional behavior; state the assumption or ask for clarification before implementing it.
- Before changing `tests/test_tasks.py`, check whether an existing test already covers the requested `services/tasks.py` behavior. Preserve an existing test when it already provides coverage; add or modify a test only when needed to verify new behavior.

## Do not touch
- Do not change the `AppError` HTTP status mapping in `utils/errors.py` or the `@api.errorhandler(AppError)` behavior in `routes/api.py` unless the task specifically concerns error infrastructure.
- Do not move `TASKS` or `USERS` out of `services/tasks.py` or `services/users.py`; this project currently uses those module-level dictionaries as its data store.
- Do not read or edit any other copy of this project, such as `Desktop\task-manager-OLD-PA5-BACKUP\repo` or `Downloads\task-manager\task-manager`; confirm the repository root with `git rev-parse --show-toplevel` before editing `services/users.py`, `routes/api.py`, or anything in `tests/`.
- Do not modify the `USERS` seed records, `NOTIFICATION_PREFS`, or `DEFAULT_NOTIFICATION_PREF` in `services/users.py` when adding or changing service functions in that file; data-layer and service-layer changes to `services/users.py` are separate steps.
- Do not fix unrelated existing Ruff findings in `app.py`, `routes/api.py`, or `tests/test_tasks.py` while completing a scoped service task.

## Hooks
`.claude/hooks/guard_writes.py`, registered in `.claude/settings.json` for Write, Edit, MultiEdit, NotebookEdit, Bash and PowerShell, blocks any write to `utils/errors.py`, `requirements.txt`, `.env` files, `migrations/`, `PLAN_LOG.md`, `plans/` and `handoffs/`, whether it comes from a file tool or from a shell redirect, `tee`, `cp`, `mv` or `sed -i`. It also blocks `DROP TABLE` and `TRUNCATE TABLE`, `rm -rf` and git force-push in shell commands, and any `postgresql://` or `sqlite:///` string written into `services/tasks.py`, because connection strings come from environment variables. When a hook blocks a call, do not retry with another tool or path spelling; ask the user. To add a rule, add the path or pattern to the constants at the top of `guard_writes.py`, then pipe a sample tool call as JSON into the script on stdin and check that a blocked call exits 2 with a message on stderr and a harmless control exits 0. Finish with a real Claude Code run that tries the blocked action, and record both results in `HOOK_LOG.md`, because a rule the settings matcher does not select enforces nothing.
