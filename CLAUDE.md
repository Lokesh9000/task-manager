# Task Manager

Python Flask API for managing tasks and users.

## Commands
- Install dependencies: `python -m pip install -r requirements.txt`.
- Run the full test suite with `python -m pytest -v`; the current baseline is 4 passing tests in `tests/test_tasks.py`.
- Run lint with `python -m ruff check .`. The starting codebase has 6 existing Ruff findings, so do not introduce new findings or perform unrelated lint cleanup.

## Architecture
- Keep the request flow layered as `routes/api.py` → `services/*.py` → the module-level data stores such as `TASKS` and `USERS`.
- Route functions in `routes/api.py` should handle HTTP concerns and call service functions rather than duplicating task or user logic.
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



