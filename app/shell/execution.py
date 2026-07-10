"""
Execution — runs external programs as child processes.
 
Resolves the command name via find_executable(), then delegates
to subprocess.run(). Error handling covers the three failure modes
that can occur between resolution and execution.
 
Depends on: command_resolution (find_executable).
"""

import os
import sys
from .command_resolution import find_executable, BUILTINS
from subprocess import Popen, PIPE, run


def exec_pipe(segments: list[list[str]]):
    prev_stdin = None
    for i, segment in enumerate(segments):
        cmd = segment[0]
        args = segment[1:]
        is_last = (i == len(segments) - 1)
        r, w = -1, -1
        if cmd in BUILTINS:
            if not is_last:
                r, w = os.pipe()

            pid = os.fork()

            if pid == 0:
                # Child-Process
                if prev_stdin is not None:
                    os.dup2(prev_stdin.fileno(), 0)
                    prev_stdin.close()

                if not is_last:
                    os.close(r)       # Child does not read
                    os.dup2(w, 1)     # stdout → Pipe
                    os.close(w)       # Origin FD not needed anymore

                BUILTINS[cmd](*args)
                os._exit(0)           # Kill Child-Process
            else:
                #Parent-Process
                if prev_stdin is not None:
                    prev_stdin.close()

                if not is_last:
                    os.close(w)       # Parent does not write
                    prev_stdin = os.fdopen(r) # Fill prev_stdin for following proc
                else:
                    os.waitpid(pid, 0) # Wait for Child-Process
        else:
            proc = Popen(segment, stdin=prev_stdin, stdout=PIPE if not is_last else None)

            if prev_stdin is not None:
                prev_stdin.close()    # SIGPIPE ermöglichen

            if is_last:
                proc.wait()
            else:
                prev_stdin = proc.stdout



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
        run([cmd] + args, executable=resolved, stdout=stdout, stderr=stderr)
    except FileNotFoundError:
        print(f"{cmd}: command not found", file=stderr or sys.stderr)
    except PermissionError:
        print(f"{cmd}: permission denied", file=stderr or sys.stderr)
    except OSError as e:
        print(f"Error executing {cmd}: {e}", file=stderr or sys.stderr)
