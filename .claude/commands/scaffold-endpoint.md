# Scaffold one API endpoint from a resource name and an HTTP method; use it to add a new route that follows the existing layers, not to change existing endpoints or add a database.

## Goal
Add one endpoint for the resource and HTTP method in `$ARGUMENTS`. It takes exactly two values, `<resource> <METHOD>`, for example `/project:scaffold-endpoint tags POST`. The files involved, derived from this repository:

- Route: `routes/api.py`. Add one handler to the existing blueprint (served under `/api`). The handler only reads the request, checks its shape, calls the service and returns the response.
- Service: `services/<resource>.py`. Create it if it does not exist, otherwise add to it, and reuse an existing service function when one already fits (for example `create_user()` in `services/users.py`). All business logic and validation live here, using `NotFoundError` and `ValidationError`.
- Schema: this project has no `schemas/` directory. Request validation lives in the service functions today. Create `schemas/<resource>.py` only if the new endpoint has a structured request body that needs field definitions the service cannot reasonably hold. If the service already validates the input, create no schema file and say so in your report.
- Tests: `tests/test_api.py` for the HTTP behavior and, when you add a service function, the matching service test file.

Before changing anything, check `$ARGUMENTS`. If it does not contain exactly two values, if the method is not one of GET, POST, PUT, PATCH or DELETE, or if the resource is not a single lowercase word, stop and ask what was meant. Do not guess, and change no files.

## Context
- Canonical pattern: the assignment names `routes/tasks.py` as the pattern to copy. That file does not exist in this repository. Its role is played by `routes/api.py`, which holds the task routes (`get_task_route`, `update_task_route`, `list_tasks_route`, `create_task_route`) and the user routes. Follow those. Do not create `routes/tasks.py`.
- Body checks: `update_task_route` rejects a body that is not a JSON object with `ValidationError("request body", "must be a JSON object")` and a missing key with `ValidationError(<key>, "is required")`. Those are checks on the shape of the request, so they belong in the route. Everything else belongs in the service.
- Errors: any `AppError` raised in a service becomes `{"error": message}` with its status code through the existing handler. Do not add error handling to the route.
- Status codes used by this app: a create returns 201, reads and updates return 200.
- Tests: `tests/test_api.py` uses an `app.test_client()` fixture and autouse fixtures that restore `TASKS` and `USERS`. Follow them so tests do not leak state.

## Constraints
- No business logic in route handlers: no validation of field values, no data-store access, no branching on business rules.
- Check that the endpoint does not already exist (look at the `@api.route` decorators in `routes/api.py`). If it does, stop and report it.
- Keep it minimal and consistent with the app: one endpoint, no new dependencies, no change to `requirements.txt`, no database, no change to existing routes, the `AppError` handler or `utils/errors.py`.

## Verification
- Run `.venv/Scripts/python -m pytest -q`. All existing tests must still pass, plus the new ones.
- Add a happy-path test that sends a valid request to the new endpoint and asserts the exact HTTP status (201 for POST, 200 for GET, PUT, PATCH and DELETE) and the response body.
- Add at least one error-path test that triggers an existing `AppError` and asserts its status code and message.
- Report the files created or changed, which of route, service and schema you touched and why, the status codes asserted, and the `pytest -q` result line.
