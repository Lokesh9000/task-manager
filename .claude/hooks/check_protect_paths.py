"""Script-level check for protect_paths.py. Writes no file.

Run from the project root:
    python .claude/hooks/check_protect_paths.py

Each case is sent to the hook script on stdin, the way Claude Code sends a
tool call, and the exit code is compared with the expected one
(2 = blocked, 0 = allowed). Exits 1 if any case differs.
"""
import json
import os
import subprocess
import sys

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "protect_paths.py")
ROOT = os.path.realpath(os.path.join(os.path.dirname(HOOK), "..", ".."))
OUTSIDE = os.path.join(os.path.dirname(ROOT), "outside-project", "utils", "errors.py")

CASES = [
    # (description, tool_name, path key, path, cwd, expected exit code)
    ("relative protected file", "Edit", "file_path", "utils/errors.py", ROOT, 2),
    ("absolute protected file", "Edit", "file_path", os.path.join(ROOT, "utils", "errors.py"), ROOT, 2),
    ("forward-slash absolute path", "Write", "file_path", ROOT.replace("\\", "/") + "/requirements.txt", ROOT, 2),
    ("PLAN_LOG.md", "Write", "file_path", "PLAN_LOG.md", ROOT, 2),
    ("existing file in plans/", "Edit", "file_path", "plans/session1-original-plan.md", ROOT, 2),
    ("new file in plans/", "Write", "file_path", "plans/new-plan.md", ROOT, 2),
    ("new nested file in handoffs/", "Write", "file_path", "handoffs/sub/new.md", ROOT, 2),
    ("the plans directory itself", "Write", "file_path", "plans", ROOT, 2),
    ("traversal inside project", "Edit", "file_path", "services/../utils/errors.py", ROOT, 2),
    ("traversal out and back in", "Edit", "file_path", os.path.join(ROOT, "..", os.path.basename(ROOT), "utils", "errors.py"), ROOT, 2),
    ("dot segments", "Edit", "file_path", "./utils/./errors.py", ROOT, 2),
    ("relative path from a subdirectory", "Edit", "file_path", "../utils/errors.py", os.path.join(ROOT, "services"), 2),
    ("relative path from utils/", "Edit", "file_path", "errors.py", os.path.join(ROOT, "utils"), 2),
    ("NotebookEdit notebook_path", "NotebookEdit", "notebook_path", "plans/notes.ipynb", ROOT, 2),
    ("no path in tool input", "Edit", "file_path", "", ROOT, 2),
    ("services/tasks.py", "Edit", "file_path", "services/tasks.py", ROOT, 0),
    ("routes/api.py", "Edit", "file_path", "routes/api.py", ROOT, 0),
    ("CLAUDE.md stays editable", "Edit", "file_path", "CLAUDE.md", ROOT, 0),
    ("DECOMPOSITION.md stays editable", "Edit", "file_path", "DECOMPOSITION.md", ROOT, 0),
    ("RETRO.md stays editable", "Write", "file_path", "RETRO.md", ROOT, 0),
    ("other file in utils/", "Write", "file_path", "utils/__init__.py", ROOT, 0),
    ("similar name: utils/errors.py.bak", "Write", "file_path", "utils/errors.py.bak", ROOT, 0),
    ("similar name: plans-old/x.md", "Write", "file_path", "plans-old/x.md", ROOT, 0),
    ("similar name: tests/requirements.txt", "Write", "file_path", "tests/requirements.txt", ROOT, 0),
    ("same relative path outside project", "Write", "file_path", OUTSIDE, ROOT, 0),
]

if os.name == "nt":
    CASES += [
        ("upper-case spelling", "Edit", "file_path", "UTILS/ERRORS.PY", ROOT, 2),
        ("backslash separators", "Edit", "file_path", "utils\\errors.py", ROOT, 2),
        ("Git Bash drive path", "Edit", "file_path", "/" + ROOT[0].lower() + ROOT[2:].replace("\\", "/") + "/utils/errors.py", ROOT, 2),
        ("trailing dot", "Edit", "file_path", "utils/errors.py.", ROOT, 2),
        ("trailing space", "Write", "file_path", "requirements.txt ", ROOT, 2),
        ("alternate data stream", "Write", "file_path", "utils/errors.py::$DATA", ROOT, 2),
    ]


def run_case(tool_name: str, key: str, path: str, cwd: str) -> tuple[int, str]:
    """Send one tool call to the hook script.

    Args:
        tool_name: The tool name to report.
        key: The tool_input key that carries the path.
        path: The path to send. An empty string sends no path at all.
        cwd: The working directory to report.

    Returns:
        The hook's exit code and its stderr text.
    """
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool_name, "cwd": cwd,
               "tool_input": {key: path} if path else {}}
    env = {**os.environ, "CLAUDE_PROJECT_DIR": ROOT}
    result = subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                            capture_output=True, text=True, env=env, check=False)
    return result.returncode, result.stderr.strip()


def main() -> int:
    """Run every case and print one line per case.

    Returns:
        0 when every case matches its expected exit code, otherwise 1.
    """
    failures = 0
    for description, tool_name, key, path, cwd, expected in CASES:
        actual, _ = run_case(tool_name, key, path, cwd)
        status = "ok  " if actual == expected else "FAIL"
        failures += actual != expected
        shown = os.path.relpath(path, ROOT) if os.path.isabs(path) else path
        print(f"{status} expected={expected} actual={actual} {tool_name:<12} {description}: {shown!r}")
    bad_code = subprocess.run([sys.executable, HOOK], input="not json",
                              capture_output=True, text=True, check=False).returncode
    status = "ok  " if bad_code == 2 else "FAIL"
    failures += bad_code != 2
    print(f"{status} expected=2 actual={bad_code} (none)       unparseable stdin")
    print(f"{len(CASES) + 1 - failures} of {len(CASES) + 1} cases as expected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
