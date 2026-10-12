"""PreToolUse hook: block file-editing tools from touching protected paths.

Claude Code runs this script before Edit, Write and NotebookEdit calls and
passes the tool call as JSON on stdin. Exit code 2 blocks the call and sends
stderr back to Claude; exit code 0 lets the call continue.

Only the file-editing tools named above are covered. Writes made through
shell commands (Bash, PowerShell) are not inspected by this hook.
"""
import json
import os
import re
import sys

PROTECTED_FILES = ("utils/errors.py", "requirements.txt", "PLAN_LOG.md")
PROTECTED_DIRS = ("plans", "handoffs")
PATH_KEYS = ("file_path", "notebook_path")

BLOCK = 2
ALLOW = 0


def project_root() -> str:
    """Return the resolved project root directory.

    Returns:
        The real path of CLAUDE_PROJECT_DIR, or of the directory two levels
        above this script when the variable is not set.
    """
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    if not root:
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    return os.path.realpath(_from_posix_drive(root))


def _from_posix_drive(path: str) -> str:
    """Convert a Git Bash style path such as /c/Users/x to C:/Users/x on Windows.

    Args:
        path: The path as given.

    Returns:
        The path with a drive letter on Windows, otherwise unchanged.
    """
    if os.name == "nt":
        match = re.match(r"^/([A-Za-z])(/.*)?$", path)
        if match:
            return f"{match.group(1)}:{match.group(2) or '/'}"
    return path


def _clean_components(path: str) -> str:
    """Remove Windows spellings that name the same file as a plain path.

    Windows ignores trailing dots and spaces in a path component and treats
    "name::$DATA" or "name:stream" as the file "name". Stripping them means
    such spellings cannot be used to slip past the comparison.

    Args:
        path: The path as given.

    Returns:
        The path with those spellings removed on Windows, otherwise unchanged.
    """
    if os.name != "nt":
        return path
    drive, rest = os.path.splitdrive(path.replace("/", "\\"))
    parts = []
    for part in rest.split("\\"):
        if part not in (".", ".."):
            part = part.split(":", 1)[0].rstrip(". ")
        parts.append(part)
    return drive + "\\".join(parts)


def relative_to_root(raw_path: str, cwd: str, root: str) -> str | None:
    """Resolve a tool path and express it relative to the project root.

    Args:
        raw_path: The path from the tool call, absolute or relative.
        cwd: The working directory relative paths are resolved against.
        root: The resolved project root.

    Returns:
        The resolved path relative to the root, lower-cased on Windows and
        using forward slashes, or None when it is outside the project.
    """
    path = _clean_components(_from_posix_drive(raw_path))
    if not os.path.isabs(path):
        path = os.path.join(_from_posix_drive(cwd), path)
    resolved = os.path.normcase(os.path.realpath(path))
    root = os.path.normcase(root)
    try:
        if os.path.commonpath([resolved, root]) != root:
            return None
    except ValueError:
        return None
    return os.path.relpath(resolved, root).replace("\\", "/")


def protected_reason(relative: str) -> str | None:
    """Say why a project-relative path is protected, if it is.

    Args:
        relative: A resolved path relative to the project root.

    Returns:
        The protected file or directory that matched, or None.
    """
    for name in PROTECTED_FILES:
        if relative == os.path.normcase(name).replace("\\", "/"):
            return name
    for name in PROTECTED_DIRS:
        prefix = os.path.normcase(name).replace("\\", "/")
        if relative == prefix or relative.startswith(prefix + "/"):
            return name + "/"
    return None


def main() -> int:
    """Check one tool call read from stdin.

    Returns:
        2 to block the call, 0 to allow it.
    """
    try:
        payload = json.load(sys.stdin)
        tool_input = payload["tool_input"]
        raw_path = next(tool_input[key] for key in PATH_KEYS if tool_input.get(key))
        if not isinstance(raw_path, str):
            raise TypeError("path is not a string")
    except (ValueError, KeyError, TypeError, AttributeError, StopIteration) as exc:
        print(f"protect_paths: blocked, could not read the target path ({exc!r}).",
              file=sys.stderr)
        return BLOCK

    root = project_root()
    relative = relative_to_root(raw_path, payload.get("cwd") or root, root)
    if relative is None:
        return ALLOW
    reason = protected_reason(relative)
    if reason is None:
        return ALLOW
    print(f"protect_paths: blocked {payload.get('tool_name', 'tool')} on '{raw_path}'. "
          f"'{reason}' is a protected path in this project (see CLAUDE.md, Do not touch). "
          "Do not retry with another tool or path spelling; ask the user instead.",
          file=sys.stderr)
    return BLOCK


if __name__ == "__main__":
    sys.exit(main())
