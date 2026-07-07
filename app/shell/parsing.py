"""
Parsing module — transforms raw input into structured tokens and
extracts redirection operators.

No dependencies on other shell modules. Only stdlib (enum, dataclasses).
This makes it the foundation layer that everything else builds on.
"""

from enum import Enum, auto
from dataclasses import dataclass, field


class ParseState(Enum):
    """
    Finite state machine for shell token parsing.

    Why an Enum instead of plain strings ("normal", "single_quote", ...):
    - Typos like ParseState.NROMAL fail at attribute lookup → immediate error
    - match/case exhaustiveness — the compiler-like structure catches
      missing states during development
    - Closed set: no one can invent ParseState.MAGIC at runtime
    """
    NORMAL = auto()
    IN_SINGLE = auto()
    IN_DOUBLE = auto()
    ESCAPE = auto()


@dataclass
class RedirectionResult:
    """
    Bundles the output of extract_redirections() into a named structure.

    Why a dataclass instead of a 5-element tuple:
    - result.stdout_target reads better than result[1]
    - Adding a field (e.g. pipe_segments) won't break every call site
    - Typos like result.stdot_target raise AttributeError immediately
    - Default values document the "nothing redirected" baseline
    """
    clean_args: list = field(default_factory=list)
    stdout_target: str | None = None
    stderr_target: str | None = None
    stdout_append: bool = False
    stderr_append: bool = False


def parse_line(line: str) -> list[str]:
    """
    Split a raw input line into tokens, respecting quoting and escaping.

    Implements a finite state machine that walks the input character by
    character. Each state determines how the next character is interpreted:
    - NORMAL: whitespace splits tokens, quotes change state
    - IN_SINGLE: everything is literal until closing '
    - IN_DOUBLE: like single but \\ escapes certain characters
    - ESCAPE: next character is literal (context-dependent in double quotes)

    Args:
        line: Raw input string from the user.

    Returns:
        List of parsed tokens with quotes and escapes resolved.
    """
    state = ParseState.NORMAL
    current = []
    tokens = []
    # Track whether we entered ESCAPE from inside double quotes —
    # because escape rules differ: in double quotes only \\, ", $, newline
    # are special; outside, everything after \\ is literal
    escape_from_double = False

    for ch in line:
        match state:
            case ParseState.NORMAL:
                if ch == '\\':
                    state = ParseState.ESCAPE
                elif ch == "'":
                    state = ParseState.IN_SINGLE
                elif ch == '"':
                    state = ParseState.IN_DOUBLE
                elif ch.isspace():
                    if current:
                        tokens.append("".join(current))
                        current = []
                else:
                    current.append(ch)

            case ParseState.IN_SINGLE:
                if ch == "'":
                    state = ParseState.NORMAL
                else:
                    current.append(ch)

            case ParseState.IN_DOUBLE:
                if ch == '"':
                    state = ParseState.NORMAL
                elif ch == '\\':
                    state = ParseState.ESCAPE
                    escape_from_double = True
                else:
                    current.append(ch)

            case ParseState.ESCAPE:
                if escape_from_double:
                    # POSIX rule: inside double quotes, backslash only
                    # escapes \\, ", $, and newline. Everything else
                    # keeps the backslash as a literal character.
                    if ch in ('\\', '"', '$', '\n'):
                        current.append(ch)
                    else:
                        current.append('\\')
                        current.append(ch)
                    state = ParseState.IN_DOUBLE
                    escape_from_double = False
                else:
                    # Outside quotes: backslash makes ANY next char literal
                    current.append(ch)
                    state = ParseState.NORMAL

    # Flush the last token if the line didn't end on whitespace
    if current:
        tokens.append("".join(current))

    return tokens


# -- Redirection operator lookup table --
# Maps operator strings to (channel, append?) tuples.
# Defined at module level because it's constant — no reason to rebuild
# it on every call to extract_redirections().
_REDIRECT_OPERATORS = {
    ">":   ("stdout", False),
    "1>":  ("stdout", False),
    ">>":  ("stdout", True),
    "1>>": ("stdout", True),
    "2>":  ("stderr", False),
    "2>>": ("stderr", True),
}


def extract_redirections(args: list[str]) -> RedirectionResult:
    """
    Separate redirection operators from regular arguments.

    Scans the token list for known operators (>, >>, 2>, etc.) and
    extracts their targets. Everything else becomes clean_args.

    Args:
        args: Token list (output of parse_line, minus the command name).

    Returns:
        RedirectionResult with clean args and any redirection targets.
    """
    handles: dict[str, str | None] = {"stdout": None, "stderr": None}
    appends = {"stdout": False, "stderr": False}
    clean_args = []

    i = 0
    while i < len(args):
        op = _REDIRECT_OPERATORS.get(args[i])
        if op is not None and i + 1 < len(args):
            channel, append = op
            handles[channel] = args[i + 1]   # next token = filename
            appends[channel] = append
            i += 2                            # skip operator + target
        else:
            # Regular argument OR an operator without a following filename —
            # either way, advance by exactly one to avoid infinite loops
            clean_args.append(args[i])
            i += 1

    return RedirectionResult(
        clean_args=clean_args,
        stdout_target=handles["stdout"],
        stderr_target=handles["stderr"],
        stdout_append=appends["stdout"],
        stderr_append=appends["stderr"],
    )