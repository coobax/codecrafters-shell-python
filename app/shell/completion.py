"""
Tab completion — provides readline-based command name completion.

Searches BUILTINS first, then EXECS. Handles both single matches
(auto-complete with trailing space) and multiple matches (display list).

Depends on: command_resolution (BUILTINS, EXECS).
"""

import readline
from .command_resolution import BUILTINS, EXECS
from collections.abc import Sequence


def _completer(text: str, state: int) -> str | None:
    """
    Readline calls this repeatedly with state=0, 1, 2, ... until it
    returns None. Each call must return the next matching command name.

    Lookup order matches bash: builtins first, then PATH executables.
    If builtins produce matches, PATH is skipped entirely — this avoids
    mixing two different namespaces in one completion list.

    Args:
        text: The partial word the user has typed so far.
        state: Readline's index into the match list (0-based).

    Returns:
        The next matching command + trailing space, or None when exhausted.
    """
    matches = [cmd for cmd in BUILTINS if cmd.startswith(text)]
    if not matches:
        matches = [cmd for cmd in EXECS if cmd.startswith(text)]

    if state < len(matches):
        # Trailing space signals readline that the token is complete —
        # the cursor jumps past the word so the user can type the next arg
        return matches[state] + " "
    return None


def _match_display_hook(substitution: str, matches: Sequence[str], longest_match_length: int,) -> None:
    """
    Called by readline when multiple completions exist and need display.

    Prints all matches on one line, then re-draws the prompt with the
    current input buffer so the user doesn't lose context.

    Args:
        substitution: The common prefix readline has already inserted.
        matches: All completion candidates.
        longest_match_length: Length of the longest match (unused but
            required by readline's callback signature).
    """
    print("")
    for match in matches:
        print(match + "  ", end="")
    print("")
    # Re-draw prompt + current input so the user sees where they are
    print("$ ", readline.get_line_buffer(), sep="", end="")
    readline.redisplay()


def init_readline() -> None:
    """
    Configure readline for tab completion.

    Called once from __main__.py at shell startup — not at import time,
    so importing this module for tests stays side-effect free.
    """
    readline.parse_and_bind("tab: complete")
    readline.set_completer(_completer)
    readline.set_completion_display_matches_hook(_match_display_hook)