# Drill 1 Prompts — Task Manager API

Use these three prompts in order. Reset services/tasks.py to its
original state between runs using: git checkout services/tasks.py

## Run 1 — No context
```
Goal: Add error handling to the process_order function
      in services/tasks.py.
Constraints: Do not change the function signature.
Verification: Run pytest tests/test_tasks.py -v when done.
```

## Run 2 — File context added
```
Goal: Add error handling to the process_order function
      in @services/tasks.py.
Context: See @services/tasks.py.
Constraints: Do not change the function signature.
Verification: Run pytest tests/test_tasks.py -v when done.
```

## Run 3 — Rich context added
```
Goal: Add error handling to the process_order function
      in @services/tasks.py.
Context: We use a custom AppError base class defined in
@utils/errors.py for all error handling — never raise raw
exceptions. See @services/users.py for the pattern we follow,
including Google-style docstrings and type hints on all functions.
Constraints: Do not change the function signature.
Verification: Run pytest tests/test_tasks.py -v when done.
```

## What to observe after each run
- What error type did Claude raise? (raw KeyError / plain Exception / AppError subclass?)
- Did Claude add a docstring? In Google style?
- Did Claude add type hints?
- How many follow-up corrections were needed?

## Setup
    pip install flask pytest
    pytest -v   # confirm 2 tests pass, 2 fail before starting
