"""
Execution — runs external programs as child processes.
 
Resolves the command name via find_executable(), then delegates
to subprocess.run(). Error handling covers the three failure modes
that can occur between resolution and execution.
 
Depends on: command_resolution (find_executable).
"""

import subprocess
import sys
from .command_resolution import find_executable

def exec_subprocess(cmd: str, args: list[str], stdout=None, stderr=None) -> None:
    """
    Run an external command as a child process.
 
    Resolves cmd to a full path first. If not found, prints an error
    to stderr (or the redirected stderr handle) and returns — no
    exception raised, matching how bash handles unknown commands.
 
    Args:
        cmd: Bare command name (e.g. "cat").
        args: Arguments to pass to the command.
        stdout: File handle for stdout redirection, or None for sys.stdout.
        stderr: File handle for stderr redirection, or None for sys.stderr.
    """

    resolved = find_executable(cmd)
    if resolved is None:
        print(f"{cmd}: command not found", file=stderr or sys.stderr)
        return
    try:
        subprocess.run([cmd] + args, executable=resolved, stdout=stdout, stderr=stderr)
    except FileNotFoundError:
        print(f"{cmd}: command not found", file=stderr or sys.stderr)
    except PermissionError:
        print(f"{cmd}: permission denied", file=stderr or sys.stderr)
    except OSError as e:
        print(f"Error executing {cmd}: {e}", file=stderr or sys.stderr)