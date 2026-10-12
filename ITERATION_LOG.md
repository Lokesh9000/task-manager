# CLAUDE.md Iteration Log

## Session 1 — October 4, 2026

### Prompt used
Add error handling to the get_task function in @services/tasks.py. Do not change the function signature. Run python -m pytest -v when done.

### What Claude did
Claude changed get_task() in services/tasks.py so an unknown task ID raises NotFoundError("Task") instead of a raw KeyError. It preserved the function signature, added a Google-style docstring following services/users.py, and imported NotFoundError from utils/errors.py. It also changed test_get_task_invalid in tests/test_tasks.py from expecting any Exception to specifically checking NotFoundError, status 404, and the "Task not found" message. The full test suite passed with 4 tests, and Ruff findings decreased from 6 to 5.

### Observation
The initial CLAUDE.md successfully guided Claude toward the error class, service style, type/documentation conventions, unchanged signature, and required verification. However, the rule telling Claude to add or update tests whenever task-service behavior changes was too broad. The existing invalid-task test already exercised get_task(), but Claude modified that test even though the prompt only requested error handling in services/tasks.py. The initial file therefore did not clearly tell Claude to preserve an existing test when it already covers the requested behavior.

### CLAUDE.md update
Changed:
`Add or update tests in tests/test_tasks.py when task-service behavior changes.`

To:
`Before changing tests/test_tasks.py, check whether an existing test already covers the requested services/tasks.py behavior. Preserve an existing test when it already provides coverage; add or modify a test only when needed to verify new behavior.`

I changed this rule because Session 1 showed that the original instruction encouraged Claude to edit an existing test even when coverage already existed.

## Session 2 — October 4, 2026

### Prompt used
Refactor create_task in @services/tasks.py to match the style of get_user in @services/users.py exactly. Run python -m pytest -v when done.

### What Claude did
Claude inspected create_task() and found that its type hints and function signature already matched the expected service style. It added only the missing Google-style docstring with Args and Returns sections. It preserved the existing behavior and did not modify tests/test_tasks.py. The full test suite passed with 4 tests, and Ruff remained at the existing 5 findings.

### Observation
This session required fewer unnecessary changes than Session 1. Claude followed services/users.py as the canonical example, preserved the existing signature and behavior, and did not modify tests because the existing tests did not need to change for a documentation-only refactor. This shows that the test-preservation rule added after Session 1 improved the guidance. Claude also correctly omitted a Raises section because create_task() does not currently raise an expected application error.

### CLAUDE.md update
No update was needed after this session. The existing architecture, convention, and test-preservation rules guided the change correctly, so adding another rule without evidence would make CLAUDE.md less focused.

## Session 3 — October 4, 2026

### Prompt used
Add a function to @services/tasks.py that returns all tasks for a given user_id. Follow the existing service pattern. Add a test for it in @tests/test_tasks.py and run python -m pytest -v when done.

### What Claude did
Claude added a service function that returns all tasks whose user_id matches the requested user. It also decided to validate the user first by calling get_user() from services/users.py, so an unknown user raises NotFoundError("User") instead of returning an empty list. Claude added two focused tests: one verifies that user 1 receives the matching tasks, and another verifies the unknown-user error. It did not add a route because the prompt only requested the service function and tests. The full test suite was independently verified with 6 tests passing.

### Observation
Session 3 required fewer corrections than Session 1 because Claude followed the service structure, kept the change scoped to the service and tests, and produced a passing implementation without unrelated edits. However, CLAUDE.md did not tell Claude what to do when requested behavior was ambiguous. Claude chose to make an unknown user raise NotFoundError even though the prompt only specified returning tasks for a user_id. The implementation is reasonable, but the behavioral decision should not be silently invented from an ambiguous requirement.

### CLAUDE.md update
Added:
`When a requested service behavior is ambiguous and existing code or tests do not establish the expected behavior, do not invent additional behavior; state the assumption or ask for clarification before implementing it.`

I added this rule because Session 3 showed that the existing conventions controlled code style well but did not control assumptions about unspecified behavior.
