# Live hook test evidence

Record of one live test of the path-protection hook (`.claude/settings.json` running
`.claude/hooks/protect_paths.py`). Everything below is taken from the transcript of that test and
from commands run immediately before and after it. The raw transcript is not stored in this
repository. Local absolute paths are replaced with `<project>`.

## Setup

- Date: 2026-10-11
- Claude Code version: 2.1.296
- Session: a fresh headless session started with `claude -p` from the project root, separate from
  the session that created the hook
- Permission mode: `acceptEdits`, with the `Read` and `Edit` tools allowed
- Instruction given to the session: use the Edit tool once to insert the comment line
  `# hook live test` as the first line of `utils/errors.py`, do not use any other tool to change
  the file, and do not retry if the edit is refused

## Attempted operation

- Protected path: `utils/errors.py`
- Tool calls made by the session: one `Read` of `utils/errors.py`, then one `Edit`
- The `Edit` call (file path given as `<project>\utils\errors.py`):

  `old_string`:

  ```
  class AppError(Exception):
      def __init__(self, message: str, status_code: int = 400):
  ```

  `new_string`:

  ```
  # hook live test
  class AppError(Exception):
      def __init__(self, message: str, status_code: int = 400):
  ```

## Result

The `Edit` call returned an error result with this message:

```
PreToolUse:Edit hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/protect_paths.py"]: protect_paths: blocked Edit on '<project>\utils\errors.py'. 'utils/errors.py' is a protected path in this project (see CLAUDE.md, Do not touch). Do not retry with another tool or path spelling; ask the user instead.
```

The session made no further tool calls and reported that the edit was refused.

## File state

| | SHA-256 of `utils/errors.py` |
|---|---|
| Before the attempt | `543040721ff2278f3a788face60d451c12e4ba56f2b75861bffe11c3a7298861` |
| After the attempt | `543040721ff2278f3a788face60d451c12e4ba56f2b75861bffe11c3a7298861` |

`git diff -- utils/errors.py` produced no output after the attempt.

## Limits of this test

- Live interception was verified for `Edit` only. `Write` and `NotebookEdit` are named in the
  hook matcher and are covered by the script-level check
  (`python .claude/hooks/check_protect_paths.py`), but neither was exercised in a live session.
- Only one protected path, `utils/errors.py`, was tried live. The other protected paths
  (`requirements.txt`, `PLAN_LOG.md`, `plans/`, `handoffs/`) are covered by the script-level check
  only.
- The hook does not inspect Bash or PowerShell commands. Writes to protected paths made through a
  shell are not covered.
- This was a single run on Windows with one Claude Code version.
