"""
Tab completion — provides readline-based command name completion.

Searches BUILTINS first, then EXECS. Handles both single matches
(auto-complete with trailing space) and multiple matches (display list).

Depends on: command_resolution (BUILTINS, EXECS).
"""

import os
import readline
from .command_resolution import BUILTINS, EXECS
from collections.abc import Sequence


def _completer(text:str, state: int) -> str | None:
    if readline.get_begidx() == 0:
        matches = sorted(cmd for cmd in BUILTINS.keys() | EXECS if cmd.startswith(text))
    else:
        dirpart = os.path.dirname(text)
        basepart = os.path.basename(text)
        try:    
            entries = os.listdir(dirpart or ".")
        except OSError:
            entries = []
        matches = sorted(
                    os.path.join(dirpart, entry) 
                    for entry in entries 
                    if entry.startswith(basepart)
                    )
    if state < len(matches):
        match = matches[state]
        if len(matches) != 1:
            suffix = ""
        elif os.path.isdir(match):
            suffix = "/"
        else:
            suffix = " "
        return match + suffix
    return None


def _match_display_hook(substitution: str, matches: Sequence[str], longest_match_length: int,) -> None:
    print("")
    matches = sorted(matches)
    for match in matches:
        if os.path.isdir(match):
            print(match + "/", end="  ")
        else:
            print(match, end="  ")
    print("")
    print("$ ", readline.get_line_buffer(), sep="", end="")
    readline.redisplay()


def init_readline() -> None:
    readline.parse_and_bind("tab: complete")
    readline.set_completer(_completer)
    readline.set_completion_display_matches_hook(_match_display_hook)
    readline.set_completer_delims(" \t\n<>|&;")