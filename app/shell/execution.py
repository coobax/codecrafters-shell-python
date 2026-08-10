"""
Execution — runs commands as child processes, standalone or in pipelines.

Two entry points:
- exec_subprocess(): a single external program via subprocess.run().
- exec_pipe(): a chain of segments connected by pipes, where each
  segment may be a shell builtin or an external program.

Builtins and external commands need different machinery: an external
program is a separate executable that Popen can wire up directly, while
a builtin is a Python function living in *this* process — to give it its
own stdout without hijacking the parent shell's, it must run inside a
forked child. exec_pipe() handles both cases.

Depends on: command_resolution (find_executable, BUILTINS).
"""

import os
import sys
from .command_resolution import find_executable, BUILTINS
from subprocess import Popen, PIPE, run


def exec_pipe(segments: list[list[str]]):
    """
    Run a pipeline: connect each segment's stdout to the next's stdin.

    Walks segments left to right, threading the read-end of each pipe
    into the following stage via prev_stdin. Dispatch is by type:

    - Builtin: forked into a child (os.fork). The child redirects fd 0/1
      with os.dup2 onto the pipe ends, calls the Python function, then
      os._exit(0). os._exit — not sys.exit — because sys.exit raises
      SystemExit, which would unwind through the parent's cleanup and
      flush inherited buffers, corrupting the shell's own state. os._exit
      terminates the child immediately without touching the parent world.
    - External: launched with Popen (non-blocking), so all stages run
      concurrently — the way a real shell drives a pipeline.

    The last segment gets no PIPE on stdout: it inherits the shell's real
    stdout, so its output reaches the terminal (or a redirection). Every
    earlier stage writes into a pipe consumed by its successor.

    Closing prev_stdin in the parent after handing it off is what enables
    SIGPIPE — once the shell no longer holds the read-end, an upstream
    writer that outlives its reader is signalled to stop instead of
    blocking forever.

    Args:
        segments: Pipeline stages, each a token list [cmd, *args],
                  produced by extract_pipe_segments().

    Gotcha: fds 0 and 1 are hardcoded — only stdin/stdout are wired.
    stderr (fd 2) still flows straight to the terminal from every stage,
    matching bash's default pipe behavior.
    """
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
                if prev_stdin is not None:
                    os.dup2(prev_stdin.fileno(), 0)
                    prev_stdin.close()

                if not is_last:
                    os.close(r)       
                    os.dup2(w, 1)    
                    os.close(w)      

                BUILTINS[cmd](*args)
                os._exit(0)          
            else:
                if prev_stdin is not None:
                    prev_stdin.close()

                if not is_last:
                    os.close(w)       
                    prev_stdin = os.fdopen(r)  
                else:
                    os.waitpid(pid, 0)
        else:
            proc = Popen(segment, stdin=prev_stdin, stdout=PIPE if not is_last else None)

            if prev_stdin is not None:
                prev_stdin.close()    

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
