"""
Parsing module — transforms raw input into structured tokens and
extracts redirection operators.

No dependencies on other shell modules. Only stdlib (enum, dataclasses).
This makes it the foundation layer that everything else builds on.
"""

from enum import Enum, auto
from dataclasses import dataclass, field


class ParseState(Enum):
    NORMAL = auto()
    IN_SINGLE = auto()
    IN_DOUBLE = auto()
    ESCAPE = auto()

@dataclass
class RedirectionResult:
    clean_args: list = field(default_factory=list)
    stdout_target: str | None = None
    stderr_target: str | None = None
    stdout_append: bool = False
    stderr_append: bool = False


def parse_line(line: str) -> list[str]:
    state = ParseState.NORMAL
    current = []
    tokens = []
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
                elif ch == '|':
                    if current:
                        tokens.append("".join(current))
                    tokens.append("".join("|"))
                    current = []
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
                    if ch in ('\\', '"', '$', '\n'):
                        current.append(ch)
                    else:
                        current.append('\\')
                        current.append(ch)
                    state = ParseState.IN_DOUBLE
                    escape_from_double = False
                else:
                    current.append(ch)
                    state = ParseState.NORMAL
    if current:
        tokens.append("".join(current))

    return tokens


_REDIRECT_OPERATORS = {
    ">":   ("stdout", False),
    "1>":  ("stdout", False),
    ">>":  ("stdout", True),
    "1>>": ("stdout", True),
    "2>":  ("stderr", False),
    "2>>": ("stderr", True),
}


def extract_redirections(args: list[str]) -> RedirectionResult:
    handles: dict[str, str | None] = {"stdout": None, "stderr": None}
    appends = {"stdout": False, "stderr": False}
    clean_args = []

    i = 0
    while i < len(args):
        op = _REDIRECT_OPERATORS.get(args[i])
        if op is not None and i + 1 < len(args):
            channel, append = op
            handles[channel] = args[i + 1]  
            appends[channel] = append
            i += 2                           
        else:
            clean_args.append(args[i])
            i += 1

    return RedirectionResult(
        clean_args=clean_args,
        stdout_target=handles["stdout"],
        stderr_target=handles["stderr"],
        stdout_append=appends["stdout"],
        stderr_append=appends["stderr"],
    )


def extract_pipe_segments(args: list[str]) -> list[list[str]]:
    segments = []
    current_segment = []

    for arg in args:
        if arg == "|":
            if current_segment:
                segments.append(current_segment)
                current_segment = []
        else:
            current_segment.append(arg)

    if current_segment:
        segments.append(current_segment)

    return segments

def extract_background(args: list[str]) -> tuple[list[str], bool]:
    if args and args[-1] == "&":
        return args[:-1], True
    return args, False