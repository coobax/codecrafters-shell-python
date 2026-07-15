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
            # Directory doesn't exist or isn't readable — skip silently,
            # just like bash does with broken PATH entries
            continue


# -- Builtin command implementations --
# Each function's signature mirrors how it's called from the main loop:
# BUILTINS[command_name](*clean_args)
# Output goes through print() so redirect_stdout in __main__.py can
# capture it transparently — no file handle parameter needed.

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
    if args and args[0] == '-r':
        readline.read_history_file(args[1])
    elif args and args[0]== '-w':
        readline.write_history_file(args[1])
    else:
        for n in range(1, readline.get_current_history_length() + 1):
           history_item = readline.get_history_item(n)
           print("{:>4}  {}".format(n, history_item))

            
    
    
    


# -- Public registries --

BUILTINS = {
    "exit": _exit,
    "echo": _echo,
    "type": _type,
    "pwd":  _pwd,
    "cd":   _cd,
    "history": _history,
}

EXECS: set[str] = set()