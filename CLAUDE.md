# Task Manager

Python Flask API for managing tasks and users.

## Commands
- Install dependencies: `python -m pip install -r requirements.txt`.
- Run the full test suite with `python -m pytest -v` (`.venv/Scripts/python -m pytest -q` with the project virtual environment); the current baseline is 183 passing tests: 127 in `tests/test_tasks.py` and 56 in `tests/test_notifications.py`.
- Run lint with `python -m ruff check .`. The codebase has 5 existing Ruff findings (`app.py` I001; `routes/api.py` I001 and F401; `tests/test_tasks.py` I001 and B017), so do not introduce new findings or perform unrelated lint cleanup.
- Before finishing a change, also run `git diff --check` (expect no output) and `git status --short` (expect only the files the task names).
- Check the path-protection hook with `python .claude/hooks/check_protect_paths.py`; it writes no file and exits 0 when every case behaves as expected.

## Architecture
- Keep the request flow layered as `routes/api.py` → `services/*.py` → the module-level data stores such as `TASKS` and `USERS`.
- Route functions in `routes/api.py` should handle HTTP concerns and call service functions rather than duplicating task or user logic.
- `routes/api.py` is one blueprint mounted at `/api` by `app.py`. It serves `/tasks` (GET with optional `?priority=`, POST), `/tasks/<id>` (GET, PATCH priority), `/users` (GET), `/users/<id>` (GET) and `/users/<id>/notifications` (GET, PATCH).
- `services/tasks.py` owns task priority (1 to 5, default 3); `services/users.py` owns the notification preference (`email`, `sms`, `none`; default `none`).
- Layer boundary enforced by the Task 2 decomposition: functions in `services/` own all validation, lookups and data-store writes and raise `AppError` subclasses, while `routes/api.py` only reads the request, calls one service function and serialises the result; `update_notification_pref` in `services/users.py` is the canonical pattern.
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
- Do not add new packages to `requirements.txt` unless the task explicitly requires a dependency.
- Do not fix unrelated existing Ruff findings in `app.py`, `routes/api.py`, or `tests/test_tasks.py` while completing a scoped service task.
- When a task is limited to tests (`tests/test_notifications.py` or `tests/test_tasks.py`), do not edit `services/users.py`, `services/tasks.py` or `routes/api.py` to make a test pass; keep the failing test and report which file is at fault.
- When a task is limited to `routes/api.py`, do not edit `services/users.py` or `services/tasks.py`; if a service function is missing or wrong, stop and report it.
- When a task is limited to `services/users.py`, do not edit `routes/api.py` or any file under `tests/`.
- Do not create or overwrite project files with shell redirection or heredocs (for example `cat > services/users.py`); use the Edit or Write tools so the path-protection hook sees the change.
- Protected paths: `utils/errors.py`, `requirements.txt`, `PLAN_LOG.md`, `plans/` and `handoffs/`. A PreToolUse hook (`.claude/settings.json` running `.claude/hooks/protect_paths.py`) blocks Edit, Write and NotebookEdit on them. The hook does not inspect shell commands, so do not write to these paths through Bash or PowerShell either. If a task needs one of them changed, stop and ask the user.
- `PLAN_LOG.md`, `plans/`, `handoffs/` and the completed sections of `DECOMPOSITION.md` are recorded evidence of earlier work; do not rewrite them.



