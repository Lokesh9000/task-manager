"""PreToolUse hook: block protected-path writes, connection strings and risky shell commands.

Claude Code runs this script before Write, Edit, MultiEdit, NotebookEdit, Bash
and PowerShell calls and passes the tool call as JSON on stdin. Exit code 2
blocks the call and sends stderr back to Claude; exit code 0 lets it continue.

What it blocks:

1. File tools (Write, Edit, MultiEdit, NotebookEdit) whose target path is one of
   the protected paths below. The path is resolved with realpath and
   os.path.normcase, so ".." segments, symlinks and, on Windows, any
   capitalization of the name compare equal.
2. File tools that put a database connection string (postgresql:// or
   sqlite:///) into services/tasks.py. Write inspects "content", Edit inspects
   "new_string" and MultiEdit inspects every edit's "new_string".
3. Shell commands (Bash, PowerShell) that
   - contain DROP TABLE, TRUNCATE TABLE or DROP DATABASE,
   - run rm with both a recursive and a force flag (or Remove-Item -Recurse -Force),
   - run git push with --force, --force-with-lease, -f or a +refspec,
   - write to a protected path through a redirection (>, >>), tee, cp, mv, rm,
     sed -i, perl -i, dd of=, truncate, shred or a PowerShell writer such as
     Set-Content or Out-File, or
   - run inline interpreter code (python -c, node -e, perl -e, powershell
     -Command) that names a protected path.

Known limits: a path built at run time (variables the hook cannot see, string
concatenation inside python -c, base64), a script file run by name, and Git
commands that rewrite files (git checkout, git restore, git apply) are not
understood. Case is folded with os.path.normcase for real paths and with
lower() for shell text; on a case-insensitive filesystem that is not Windows,
file-tool paths in a different case are not folded.
"""
import glob
import json
import os
import re
import shlex
import sys

PROTECTED_FILES = ("utils/errors.py", "requirements.txt", "PLAN_LOG.md")
PROTECTED_DIRS = ("plans", "handoffs", "migrations")
ENV_FILE = re.compile(r"^\.env(?:\.(?!(?:example|sample|template)$)[^/]+)?$", re.IGNORECASE)
PATH_KEYS = ("file_path", "notebook_path")
SHELL_TOOLS = ("Bash", "PowerShell")

CONTENT_GUARDED_FILE = "services/tasks.py"
CONNECTION_STRING = re.compile(r"postgresql(?:\+\w+)?://|sqlite(?:\+\w+)?:///", re.IGNORECASE)
DESTRUCTIVE_SQL = re.compile(r"\b(?:drop|truncate)\s+(?:table|database)\b", re.IGNORECASE)

WRAPPERS = {"sudo", "env", "command", "nohup", "time", "exec", "xargs", "nice", "doas", "builtin"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "ash"}
POWERSHELLS = {"powershell", "pwsh"}
INTERPRETERS = re.compile(r"^(?:python[\d.]*|py|node|perl|ruby|php|pwsh|powershell|cmd)$")
INLINE_FLAGS = {"-c", "-e", "-r", "-command", "-encodedcommand", "/c"}
OPERATOR = re.compile(r"^[();<>|&]+$")
UNIX_ALL_ARGS = {"tee", "rm", "unlink", "rmdir", "shred", "truncate", "mv"}
UNIX_LAST_ARG = {"cp", "install", "ln"}
PS_REMOVE = {"remove-item", "ri", "rm", "rmdir", "rd", "del", "erase"}
PS_COPY = {"copy-item", "copy", "cp", "cpi"}
PS_WRITE = {"set-content", "add-content", "out-file", "clear-content", "move-item", "new-item",
            "rename-item", "tee-object", "sc", "ac", "ni", "mi", "move", "mv", "ren", "rni"}

BLOCK = 2
ALLOW = 0
MAX_DEPTH = 3
ENV_MESSAGE = ("Database connection strings come from environment variables "
               "(read os.environ[\"DATABASE_URL\"]); never write one into source code.")


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
    if ENV_FILE.match(relative.rsplit("/", 1)[-1]):
        return ".env"
    return None


def new_content(tool_input: dict) -> list[str]:
    """Collect the text a file tool would add to a file.

    Args:
        tool_input: The tool_input object of a file-tool call.

    Returns:
        The Write content, the Edit new_string and every MultiEdit edit's
        new_string. Text being removed (old_string) is not collected.
    """
    texts = [tool_input.get(key) for key in ("content", "new_string", "new_source")]
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        texts += [edit.get("new_string") for edit in edits if isinstance(edit, dict)]
    return [text for text in texts if isinstance(text, str)]


def check_file_tool(tool: str, tool_input: dict, cwd: str, root: str) -> str | None:
    """Check a file-tool call against the path guard and the content guard.

    Args:
        tool: The tool name.
        tool_input: The tool_input object.
        cwd: The working directory.
        root: The resolved project root.

    Returns:
        A message explaining the block, or None to allow.
    """
    raw_path = next((tool_input[key] for key in PATH_KEYS if tool_input.get(key)), None)
    if not isinstance(raw_path, str):
        return "could not read the target path of this call"
    relative = relative_to_root(raw_path, cwd, root)
    if relative is None:
        return None
    reason = protected_reason(relative)
    if reason:
        return (f"{tool} on '{raw_path}' is blocked. '{reason}' is a protected path in this "
                "project (see CLAUDE.md, Hooks). Do not retry with another tool or path "
                "spelling; ask the user instead.")
    if relative == CONTENT_GUARDED_FILE:
        for text in new_content(tool_input):
            found = CONNECTION_STRING.search(text)
            if found:
                return (f"{tool} on '{raw_path}' is blocked: the new text contains a database "
                        f"connection string ('{found.group(0)}'). {ENV_MESSAGE}")
    return None


def tokenize(command: str, powershell: bool) -> list[str]:
    """Split a shell command into words and operators.

    Args:
        command: The command text.
        powershell: True when it is a PowerShell command, where a backslash is a
            path separator and not an escape.

    Returns:
        The tokens, with ;, &&, |, > and similar operators as separate tokens.
        Unbalanced quotes (an apostrophe inside a here-document, for example)
        fall back to a coarser split instead of failing.
    """
    text = command.replace("\r\n", "\n").replace("\n", " ; ")
    text = text.replace("\\", "/") if powershell else text.replace("`", " ; ")
    try:
        lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return [t.strip("'\"") for t in re.findall(r"[;&|<>()]+|[^\s;&|<>()]+", text)]


def split_segments(tokens: list[str]) -> list[tuple[list[str], list[str]]]:
    """Group tokens into simple commands and pull out redirection targets.

    Args:
        tokens: The output of tokenize().

    Returns:
        One (words, redirect_targets) pair per command. Input redirections and
        here-document markers are dropped.
    """
    segments: list[tuple[list[str], list[str]]] = [([], [])]
    mode = ""
    for token in tokens:
        if OPERATOR.match(token):
            if ">" in token:
                mode = "out"
            elif "<" in token:
                mode = "in"
            else:
                segments.append(([], []))
                mode = ""
        elif mode == "out":
            segments[-1][1].append(token)
            mode = ""
        elif mode == "in":
            mode = ""
        else:
            segments[-1][0].append(token)
    return segments


def _name(word: str) -> str:
    """Return the lower-case command name of a path or word."""
    return os.path.basename(word).lower().removesuffix(".exe")


def command_words(words: list[str]) -> list[str]:
    """Drop leading variable assignments and wrapper commands such as sudo or xargs.

    Args:
        words: The words of one simple command.

    Returns:
        The words starting at the command that actually runs.
    """
    i = 0
    while i < len(words):
        if re.match(r"^\w+=", words[i]):
            i += 1
        elif _name(words[i]) in WRAPPERS:
            i += 1
            while i < len(words) and words[i].startswith("-"):
                i += 1
        else:
            break
    return words[i:]


def _ps_flag(options: list[str], full: str, shortest: int) -> bool:
    """Say whether a PowerShell parameter list contains a parameter, allowing abbreviations."""
    return any(len(o) >= shortest and full.startswith(o.lower()) for o in options)


def removes_recursively_and_forced(name: str, options: list[str], powershell: bool) -> bool:
    """Say whether a remove command carries both a recursive and a force flag.

    Args:
        name: The command name.
        options: The words of the command that start with a dash.
        powershell: True to use PowerShell parameter rules.

    Returns:
        True for rm -rf (any flag order or spelling) and Remove-Item -Recurse -Force.
    """
    if powershell:
        return (name in PS_REMOVE and _ps_flag(options, "-recurse", 2)
                and _ps_flag(options, "-force", 3))
    if name != "rm":
        return False
    recursive = any(o == "--recursive" or (not o.startswith("--") and re.search("[rR]", o))
                    for o in options)
    forced = any(o == "--force" or (not o.startswith("--") and "f" in o) for o in options)
    return recursive and forced


def pushes_with_force(args: list[str]) -> bool:
    """Say whether the arguments after "git" make a forced push.

    Args:
        args: The words after the git command.

    Returns:
        True for push with --force, --force-with-lease, -f (alone or in a
        cluster such as -fu) or a refspec starting with +.
    """
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") else 1
    if i >= len(args) or args[i] != "push":
        return False
    for arg in args[i + 1:]:
        if arg == "--force" or arg.startswith("--force-with-lease"):
            return True
        if re.fullmatch(r"-[A-Za-z]+", arg) and "f" in arg:
            return True
        if len(arg) > 1 and arg.startswith("+"):
            return True
    return False


def protected_mention(text: str) -> str | None:
    """Find a protected path named anywhere in a piece of text.

    Args:
        text: Inline interpreter code or arguments.

    Returns:
        The protected name that appears in the text, or None.
    """
    text = text.lower().replace("\\", "/")
    for name in PROTECTED_FILES:
        if name.lower() in text:
            return name
    for name in PROTECTED_DIRS:
        if re.search(rf"(?<![\w.]){name}/", text):
            return name + "/"
    if re.search(r"(?<![\w.])\.env(?![a-z0-9_-])", text):
        return ".env"
    return None


def analyze(command: str, powershell: bool, depth: int = 0) -> tuple[list[str], list[str]]:
    """Inspect a shell command for destructive operations and write targets.

    Args:
        command: The command text.
        powershell: True for a PowerShell command.
        depth: Recursion depth for commands passed to bash -c, eval or powershell -Command.

    Returns:
        A pair (reasons, targets): reasons are descriptions of destructive
        commands found, targets are the paths the command writes to.
    """
    reasons: list[str] = []
    targets: list[str] = []
    for words, redirects in split_segments(tokenize(command, powershell)):
        targets += redirects
        _inspect_words(command_words(words), powershell, depth, reasons, targets)
    return reasons, targets


def _inspect_words(words: list[str], powershell: bool, depth: int,
                   reasons: list[str], targets: list[str]) -> None:
    """Add what one simple command does to the reasons and targets lists."""
    if not words:
        return
    name, args = _name(words[0]), words[1:]
    options = [a for a in args if a.startswith("-")]
    positional = [a for a in args if not a.startswith("-")]
    lowered = [a.lower() for a in args]

    if removes_recursively_and_forced(name, options, powershell):
        reasons.append("recursive forced delete (rm -rf / Remove-Item -Recurse -Force)")
    if name == "git" and pushes_with_force(args):
        reasons.append("git force-push (--force, --force-with-lease, -f or +refspec)")

    if name in SHELLS | POWERSHELLS | {"eval"} and depth < MAX_DEPTH:
        flag = "-c" if name in SHELLS else "-command"
        if name == "eval":
            inner = " ".join(args)
        else:
            inner = args[lowered.index(flag) + 1] if flag in lowered[:-1] else ""
        found = analyze(inner, name in POWERSHELLS, depth + 1)
        reasons += found[0]
        targets += found[1]
    if name == "find" and any(a in ("-exec", "-execdir") for a in args):
        start = next(i for i, a in enumerate(args) if a in ("-exec", "-execdir"))
        _inspect_words(command_words(args[start + 1:]), powershell, depth, reasons, targets)

    if name in UNIX_ALL_ARGS or (powershell and name in PS_WRITE | PS_REMOVE):
        targets += positional
    if name in UNIX_LAST_ARG or (powershell and name in PS_COPY):
        targets += positional[-1:]
    if name in ("sed", "gsed", "perl") and any(
            re.match(r"^-[A-Za-z]*i", o) or o == "--in-place" for o in options):
        targets += positional
    if name == "dd":
        targets += [a[3:] for a in args if a.startswith("of=")]
    if INTERPRETERS.match(name) and any(a in INLINE_FLAGS for a in lowered):
        mention = protected_mention(" ".join(args))
        if mention:
            reasons.append(f"inline {name} code that names the protected path '{mention}'")


def expand_target(target: str, cwd: str) -> list[str]:
    """Expand variables, ~ and wildcards in a shell write target.

    Args:
        target: The target as written in the command.
        cwd: The working directory.

    Returns:
        The target itself plus every existing path a wildcard matches.
    """
    expanded = os.path.expandvars(os.path.expanduser(target))
    paths = [expanded]
    if re.search(r"[*?\[]", expanded):
        pattern = expanded if os.path.isabs(expanded) else os.path.join(_from_posix_drive(cwd), expanded)
        paths += glob.glob(pattern)
    return paths


def check_command(tool: str, command: str, powershell: bool, cwd: str, root: str) -> str | None:
    """Check a shell command against the destructive-command and write guards.

    Args:
        tool: The tool name.
        command: The command text.
        powershell: True for the PowerShell tool.
        cwd: The working directory.
        root: The resolved project root.

    Returns:
        A message explaining the block, or None to allow.
    """
    if DESTRUCTIVE_SQL.search(command):
        return (f"{tool} command is blocked: it contains DROP/TRUNCATE TABLE (or DROP DATABASE). "
                "Destructive SQL is not run from this session; ask the user instead.")
    reasons, targets = analyze(command, powershell)
    if reasons:
        return (f"{tool} command is blocked: {reasons[0]}. Do not retry with a different "
                "spelling; ask the user instead.")
    for target in targets:
        for path in expand_target(target, cwd):
            relative = relative_to_root(path, cwd, root)
            if relative is None:
                continue
            reason = protected_reason(relative)
            if reason:
                return (f"{tool} command is blocked: it writes to '{target}', and '{reason}' is a "
                        "protected path in this project (see CLAUDE.md, Hooks). Do not retry "
                        "with another tool or path spelling; ask the user instead.")
            found = CONNECTION_STRING.search(command)
            if relative == CONTENT_GUARDED_FILE and found:
                return (f"{tool} command is blocked: it writes a database connection string "
                        f"('{found.group(0)}') to '{target}'. {ENV_MESSAGE}")
    return None


def main() -> int:
    """Check one tool call read from stdin.

    Returns:
        2 to block the call, 0 to allow it.
    """
    try:
        payload = json.load(sys.stdin)
        tool = payload.get("tool_name", "tool")
        tool_input = payload["tool_input"]
        if not isinstance(tool_input, dict):
            raise TypeError("tool_input is not an object")
        root = project_root()
        cwd = payload.get("cwd") or root
        if tool in SHELL_TOOLS:
            command = tool_input.get("command")
            if not isinstance(command, str):
                raise TypeError("command is not a string")
            problem = check_command(tool, command, tool == "PowerShell", cwd, root)
        else:
            problem = check_file_tool(tool, tool_input, cwd, root)
    except Exception as exc:  # noqa: BLE001 - fail closed: an unreadable call is not allowed
        print(f"guard_writes: blocked, could not check this call ({exc!r}).", file=sys.stderr)
        return BLOCK
    if problem:
        print(f"guard_writes: {problem}", file=sys.stderr)
        return BLOCK
    return ALLOW


if __name__ == "__main__":
    sys.exit(main())
