"""
Command resolution — decides what a command name refers to.

Owns two registries:
- BUILTINS: name → function mapping for shell-internal commands
- EXECS: set of executable names found on PATH

Also provides find_executable() for resolving a name to a full path
and _type() for reporting what a command is (analog to bash's `type`).

No dependencies on other shell modules. Only stdlib (sys, os).
"""

import sys
import os
import readline
from typing import Callable


def find_executable(exec_name: str) -> str | None:
    """
    Search PATH for an executable matching exec_name.

    Walks each directory in PATH left-to-right and returns the first
    match that is both a regular file and has execute permission.
    First match wins — same semantics as bash/POSIX.

    Args:
        exec_name: The bare command name (e.g. "cat", not "/usr/bin/cat").

    Returns:
        Absolute path to the executable, or None if not found.
    """
    for path in os.environ.get("PATH", "").split(os.pathsep):
        full_path = os.path.join(path, exec_name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None


def collect_execs() -> None:
    """
    Populate the EXECS set with all executable names found on PATH.

    Called once at shell startup from __main__.py — NOT at import time,
    so importing this module for tests or introspection stays cheap.
    """
    for path in os.environ.get("PATH", "").split(os.pathsep):
        try:
            for executable in os.listdir(path):
                full_path = os.path.join(path, executable)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    EXECS.add(executable)
        except OSError:
            continue


def _type(cmd_name: str) -> None:
    """Report whether cmd_name is a builtin, an executable, or unknown."""
    executable_path = find_executable(cmd_name)
    if cmd_name in BUILTINS:
        print(f"{cmd_name} is a shell builtin")
    elif executable_path is not None:
        print(f"{cmd_name} is {executable_path}")
    else:
        print(f"{cmd_name}: not found")

def _cd(*args: str) -> None:
    """
    Change the current working directory.

    With no args: go to $HOME (via expanduser).
    With one arg: go there (~ expansion supported).
    With 2+ args: error — matching bash behavior.
    """
    if len(args) == 0:
        target = os.path.expanduser("~")
    elif len(args) == 1:
        target = os.path.expanduser(args[0])
    else:
        print("cd: too many arguments")
        return
    try:
        os.chdir(target)
    except OSError:
        print(f"cd: {target}: No such file or directory")

def _exit(code: str = "0") -> None:
    """Exit the shell with the given status code (default 0)."""
    sys.exit(int(code))

def _echo(*args: str) -> None:
    """Print arguments separated by spaces, followed by a newline."""
    print(" ".join(args))

def _pwd() -> None:
    """Print the current working directory."""
    print(os.getcwd())

def _history(*args: str) -> None:
    """
    Implement the `history` builtin.

    Dispatch on the first argument:
    - No args: print the in-memory list, numbered 1..N (bash format).
    - `-r <path>`: read a file, append its lines to the history.
    - `-w <path>`: write the whole list to the file (created if absent).
    - `-a <path>`: append only entries added since the last `-a` to the file.

    Unknown flag or missing/extra path is a usage error, not a silent no-op.

    Args:
        args: Tokens after the command name, e.g. ("-r", "/tmp/hist").
    """

    flag = args[0] if args else None

    if flag is None:
        length = readline.get_current_history_length()

        for n in range(1, length + 1):
            print(f"{n:>4}  {readline.get_history_item(n)}")
        return
    elif flag not in _HISTORY_FLAGS:
        print(f"history {flag}: No valid option" )
        return

    if len(args) > 2:
        print(f"history {flag} {' '.join(args[2:])}: Too many arguments")
        return
    elif len(args) < 2:
        print(f"history {flag}: Option requires an argument")
        return
    
    path = args[1]
    try:
        _HISTORY_FLAGS[flag](path)
    except FileNotFoundError:
        print(f"Could not load/write history: {path}: No such file or directory")
    except PermissionError:
        print(f"Could not load/write history: {path}: Permission denied")

def append_history(path:str) -> None:
    current_history_length = readline.get_current_history_length()
    n = current_history_length - _history_state["last_appended"]
    readline.append_history_file(n, path)
    _history_state["last_appended"] = current_history_length

def load_history():
    histfile = os.environ.get('HISTFILE')
    if not histfile:
        return  
    try:
        readline.read_history_file(histfile)
    except OSError:
        pass

def save_history():
    histfile = os.environ.get('HISTFILE')
    if not histfile:
        return
    try:
        readline.write_history_file(histfile)
    except OSError:
        pass

def _jobs() -> None:
    return None


BUILTINS = {
    "exit": _exit,
    "echo": _echo,
    "type": _type,
    "pwd":  _pwd,
    "cd":   _cd,
    "history": _history,
    "jobs": _jobs,
}

EXECS: set[str] = set()

_HISTORY_FLAGS = {
    "-r": readline.read_history_file,   
    "-w": readline.write_history_file, 
    "-a": append_history,
}

_history_state = {
    "last_appended": 0,
}
