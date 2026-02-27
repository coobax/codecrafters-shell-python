import sys
import os
import subprocess
from enum import Enum, auto
from contextlib import redirect_stdout

'''
Hier werden Ideen oder aktuelle Bausteine gesammelt:
    Redirect:
          # Save original stdout
            o = sys.stdout

            # Redirect stdout to a file
            with open('output.txt', 'w') as f:
                sys.stdout = f
                for i in range(10):
                    print("printing line", i)

            # Restore stdout
            sys.stdout = o


    for i, arg in enumerate(args):
            if arg == ">" or arg == "1>":
                if i + 1 < len(args):
                    out_name = args[i + 1]
                    redirect_target = True
                    if redirect_target == True:
                        with open(out_name, 'w') as f:
                            sys.stdout = f
                            print(f"Output redirection not implemented yet\nFilename: {out_name}")
                else:
                    print(f"Syntax error: erwartet Dateiname nach '{arg}'")
                break
    
    
    Todo:
    Execution in eigener Funktion
    Command Container: main() nutzt nur noch cmd.name, cmd.args, cmd.stdout_target
'''

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

def _exec_subprocess(cmd, args:list[str], stdout=None):
    resolved = _find_executable(cmd)
    if resolved is None:
        print(f"{cmd}: command not found")
    else:
        try:
            subprocess.run([cmd] + args, executable=resolved, stdout=stdout)
        except FileNotFoundError:
            print(f"{cmd}: command not found")
        except PermissionError:
            print(f"{cmd}: permission denied")
        except OSError as e:
            print(f"Error executing {cmd}: {e}")

def _run_cmd(command_name, args, stdout=None):
    #Maybe redirect schlater setzen? Zusätzliches Arg redirect_tkn=False?
    try:
        if command_name in BUILTINS:
            if stdout is None:
                BUILTINS[command_name](*args)
            else:
                with redirect_stdout(stdout):
                    BUILTINS[command_name](*args)      
        else:
            _exec_subprocess(command_name, args, stdout = stdout)
    except Exception as e:
        raise e

BUILTINS = {
    "exit": _exit,
    "echo": _echo,
    "type": _type,
    "pwd": _pwd,
    "cd": _cd,
}

def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        try:
            line = input()
            user_Input = _parse_line(line)
        except EOFError:
            break

        if not user_Input:
            continue

        command_name = user_Input[0]

        args = user_Input[1:]

        if ">" in args or "1>" in args:
            if ">" in args:
                idx = args.index(">")
            else:
                idx = args.index("1>")
            out_name = args[idx + 1]
            args_cut = args[:idx]
            #out_name.parent.mkdir(parents=True, exist_ok=True) needs "Path" imported
            with open(out_name, 'w') as f:
                _run_cmd(command_name, args_cut, stdout = f)
            #Hier abfangen an welcher Position redir sitzt und weitergeben?        
        else:
            _run_cmd(command_name, args)


    
        
if __name__ == "__main__":
    main()
