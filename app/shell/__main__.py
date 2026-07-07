"""
Entry point for the shell package — run via `python -m shell`.

This module is the orchestrator: it initializes subsystems, runs the
REPL loop, and delegates every step to the responsible module.
No business logic lives here — only glue.
"""

import sys
from contextlib import redirect_stdout, redirect_stderr

from .completion import init_readline
from .parsing import parse_line, extract_redirections
from .command_resolution import collect_execs, BUILTINS
from .execution import exec_subprocess


def main() -> None:
    """
    Shell REPL — read, evaluate, print, loop.

    Initialization order matters: collect_execs() populates EXECS
    before init_readline() sets up the completer that searches it.
    """
    collect_execs()
    init_readline()

    while True:
        try:
            # input() handles prompt display + flush + reading in one call
            line = input("$ ")
            user_input = parse_line(line)
        except EOFError:
            break

        if not user_input:
            continue

        command_name = user_input[0]
        args = user_input[1:]
        redirections = extract_redirections(args)

        stdout = stderr = None
        try:
            if redirections.stdout_append:
                stdout = open(redirections.stdout_target, "a") if redirections.stdout_target else None
            else:
                stdout = open(redirections.stdout_target, "w") if redirections.stdout_target else None
            if redirections.stderr_append:
                stderr = open(redirections.stderr_target, "a") if redirections.stderr_target else None
            else:
                stderr = open(redirections.stderr_target, "w") if redirections.stderr_target else None

            if command_name in BUILTINS:
                # redirect_stdout/stderr wrap print() calls inside builtins
                # transparently — the builtins themselves don't need to know
                # about file handles
                with redirect_stdout(stdout or sys.stdout), redirect_stderr(stderr or sys.stderr):
                    BUILTINS[command_name](*redirections.clean_args)
            else:
                exec_subprocess(command_name, redirections.clean_args, stdout=stdout, stderr=stderr)
        except Exception as e:
            print(f"Error executing {command_name}: {e}", file=stderr or sys.stderr)
            continue
        finally:
            # Always close file handles to flush writes and free resources
            if stdout:
                stdout.close()
            if stderr:
                stderr.close()


if __name__ == "__main__":
    main()