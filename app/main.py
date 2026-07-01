import sys
import os
import subprocess
import readline
from enum import Enum, auto
from contextlib import redirect_stdout, redirect_stderr
#from dataclasses import dataclass, field
'''In Modulen und Klassen neu schreiben'''
class ParseState(Enum):

    NORMAL = auto()
    IN_SINGLE = auto()
    IN_DOUBLE = auto()
    ESCAPE = auto()

def _parse_line(line):

    state = ParseState.NORMAL
    current = []
    tokens = []

    esc_dbl = False

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
                elif ch in ("\\"):
                    state = ParseState.ESCAPE
                    esc_dbl = True
                else:
                    current.append(ch)

            case ParseState.ESCAPE:
                if esc_dbl == True:
                    if ch in ("\\", '"', "$", "\n"):
                        current.append(ch)
                    else:
                        current.append("\\")
                        current.append(ch)
                    state = ParseState.IN_DOUBLE
                    esc_dbl = False
                else:
                    current.append(ch)
                    state = ParseState.NORMAL
    if current:
        tokens.append("".join(current))

    return tokens

def _collect_execs():
    for path in os.environ.get("PATH", "").split(os.pathsep):
        try:
            for executable in os.listdir(path):
                full_path = os.path.join(path, executable)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    EXECS.add(executable)
        except OSError:
            continue

def _completer(text, state):
    matches = [cmd for cmd in BUILTINS if cmd.startswith(text)]
    if not matches:
        matches = [cmd for cmd in EXECS if cmd.startswith(text)]
    if state < len(matches):
        return matches[state] + " "
    return None

def _match_display_hook(substitution, matches, longest_match_length):
    print ("")
    for match in matches:
        print (match + "  ",end="")
    print ("")
    print ("$", readline.get_line_buffer(),end="")
    readline.redisplay()

def _find_executable(exec_name):
    for path in os.environ.get("PATH", "").split(os.pathsep):
        full_path = os.path.join(path, exec_name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None

def _type(cmd_name):
    executable_path = _find_executable(cmd_name)
    if cmd_name in BUILTINS:
        print(f"{cmd_name} is a shell builtin")
    elif executable_path is not None:
        print(f"{cmd_name} is {executable_path}")
    else:
        print(f"{cmd_name}: not found")

def _cd(*args):
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

def _exit(code=0):
    sys.exit(int(code))
    
def _echo(*args):
    print(" ".join(args))

def _pwd():
    print(os.getcwd())

def _exec_subprocess(cmd, args, stdout=None, stderr=None):
    resolved = _find_executable(cmd)
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
  
def _extract_redirections(args):
# Operator -> (Ziel-Kanal, Append?)
    REDIRECTS = {
        ">":   ("stdout", False),
        "1>":  ("stdout", False),
        ">>":  ("stdout", True),
        "1>>": ("stdout", True),
        "2>":  ("stderr", False),
        "2>>": ("stderr", True),
    }
    handles = {"stdout": None, "stderr": None}
    appends = {"stdout": False, "stderr": False}
    clean_args = []

    i = 0
    while i < len(args):
        op = REDIRECTS.get(args[i])
        if op is not None and i + 1 < len(args):
            channel, append = op
            handles[channel] = args[i + 1]   # Dateiname = nächstes Token
            appends[channel] = append
            i += 2                            # Operator + Ziel überspringen
        else:
            # normales Argument ODER ein Operator ohne folgenden Dateinamen:
            # in beiden Fällen genau ein Token weiter -> kein Hängenbleiben möglich
            clean_args.append(args[i])
            i += 1

    return (clean_args, handles["stdout"], handles["stderr"],
            appends["stdout"], appends["stderr"])

BUILTINS = {
    "exit": _exit,
    "echo": _echo,
    "type": _type,
    "pwd": _pwd,
    "cd": _cd,
}

EXECS = set()
_collect_execs()

readline.parse_and_bind("tab: complete")  
readline.set_completer(_completer)
readline.set_completion_display_matches_hook(_match_display_hook)

def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        try:
            line = input()
            user_input = _parse_line(line)
        except EOFError:
            break

        if not user_input:
            continue

        command_name = user_input[0]

        args = user_input[1:]
        
        clean_args, stdout_handle, stderr_handle, stdout_handle_append, stderr_handle_append = _extract_redirections(args)

        try:
            if stdout_handle_append:
                stdout = open(stdout_handle, "a") if stdout_handle else None
            else:
                stdout = open(stdout_handle, "w") if stdout_handle else None
            if stderr_handle_append:
                stderr = open(stderr_handle, "a") if stderr_handle else None
            else:
                stderr = open(stderr_handle, "w") if stderr_handle else None
            if command_name in BUILTINS:
                with redirect_stdout(stdout or sys.stdout), redirect_stderr(stderr or sys.stderr):
                    BUILTINS[command_name](*clean_args)
            else:
                _exec_subprocess(command_name, clean_args, stdout=stdout, stderr=stderr)
        except Exception as e:
            print(f"Error executing {command_name}: {e}", file=stderr or sys.stderr) 
            continue
        finally:
            if stdout:
                stdout.close()
            if stderr:
                stderr.close()
    
if __name__ == "__main__":
    main()