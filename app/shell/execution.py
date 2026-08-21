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
from .command_resolution import find_executable, BUILTINS, JOBS, _job_state, Job
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

def exec_background(cmd: str, args: list[str], line: str, stdout=None, stderr=None) -> None:
    resolved = find_executable(cmd)
    if resolved is None:
        print(f"{cmd}: command not found", file=stderr or sys.stderr)
        return

    try:
        proc = Popen([cmd] + args, executable=resolved, stdout=stdout, stderr=stderr)
    except OSError as e:
        print(f"Error executing {cmd}: {e}", file=stderr or sys.stderr)
        return
    
    number = _job_state["next_number"]
    JOBS[number] = Job(proc=proc, line=line)
    _job_state["next_number"] = number + 1
    print(f"[{number}] {proc.pid}")