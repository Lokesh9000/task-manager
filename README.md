# task-manager

Flask task manager used for COMP 4600/5300 PA 5 ("Plan, Decompose, and Supervise"). It started from the Week 4 project and now has task priority (Task 1), user notification preferences (Task 2), a retrospective and an updated `CLAUDE.md` (Task 3).

## Where to look

| PA 5 deliverable | File | What it holds |
|---|---|---|
| Task 1 | `PLAN_LOG.md` | Supervision log: four Plan Mode sessions, two amendments, and the places where the output did not fully match the plan. The saved plans are in `plans/`. |
| Task 2 | `DECOMPOSITION.md` | Subagent table, the four prompts as issued, the `pytest -q` result for each subagent, and the Divergence section. |
| Task 3A | `RETRO.md` | Four-paragraph retrospective. |
| Task 3B | `CLAUDE.md` | The Week 4 file, updated in place. |

`CLAUDE_v1.md`, `DRILL_PROMPTS.md`, `ITERATION_LOG.md` and `JUSTIFICATION.md` are the Week 4 files, unchanged.

## Run it

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pytest -q
```

Expected: `170 passed`. Ruff is not in `requirements.txt`; with `ruff==0.16.10` installed, `python -m ruff check .` reports the 5 findings that were already in the Week 4 code. To start the app, run `.venv/Scripts/python app.py`.

## API

All routes are under `/api`.

| Method and path | Purpose |
|---|---|
| `GET /tasks` | List tasks; `?priority=1` to `5` filters by priority |
| `POST /tasks` | Create a task; `priority` is optional and defaults to 3 |
| `GET /tasks/<id>` | Get one task |
| `PATCH /tasks/<id>` | Update a task's `priority` |
| `GET /users` | List users |
| `GET /users/<id>` | Get one user |
| `GET /users/<id>/notifications` | Get the notification preference |
| `PATCH /users/<id>/notifications` | Set it to `email`, `sms`, `none`, or `null` |

## Notes for the reader

- An unset notification preference is `null`, not the string `"none"`. The reasoning is in the "Default `none`" row of `DECOMPOSITION.md`.
- There is no database. Tasks and users are in-memory dictionaries (`TASKS`, `USERS`), so data resets when the app restarts.
- The history contains an earlier PA 5 attempt on this project. The submitted work starts at the Week 4 starter commit `442e121` and continues in the commits after it. Commit IDs cited inside `PLAN_LOG.md` are mapped to the IDs in this repository under "Audit notes" at the end of that file.
