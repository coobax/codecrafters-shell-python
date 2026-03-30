import sys
import os
import subprocess
from enum import Enum, auto
from contextlib import redirect_stdout, redirect_stderr

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

def _exec_subprocess(cmd, args, stdout=None, stderr=None):
    resolved = _find_executable(cmd)
    if resolved is None:
        print(f"{cmd}: command not found", file=stderr or sys.stderr)
    else:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                subprocess.run([cmd] + args, executable=resolved, stdout=stdout, stderr=stderr)
            except FileNotFoundError:
                print(f"{cmd}: command not found")
            except PermissionError:
                print(f"{cmd}: permission denied")
            except OSError as e:
                print(f"Error executing {cmd}: {e}")

def _run_cmd(command_name, args, stdout=None, stderr=None):
    try:
        if command_name in BUILTINS:
            with redirect_stdout(stdout or sys.stdout), redirect_stderr(stderr or sys.stderr):
                BUILTINS[command_name](*args)      
        else:
            _exec_subprocess(command_name, args, stdout=stdout, stderr=stderr)
    except Exception as e:
        raise e
    
def extract_redirections(args):
    stderr_handle = None
    stdout_handle = None
    stdout_handle_append = False
    stderr_handle_append = False
    clean_args = []
    i = 0
    while i < len(args):
        if args[i] in (">", "1>"):
            if i + 1 < len(args):
                stdout_handle = args[i + 1]
                i += 2
            else:
                i += 1
        elif args[i] in ( "1>>", ">>"):
            if  i + 1 < len(args):
                stdout_handle_append = True
                stdout_handle = args[i + 1]
                i +=2
        elif args[i] == "2>":
            if i + 1 < len(args):
                stderr_handle = args[i + 1]
                i += 2
        elif args[i] == "2>>":
            if i + 1 < len(args):
                stderr_handle = args[i + 1]
                stderr_handle_append = True
                i += 2
            else:
                i += 1      
        else:
            clean_args.append(args[i])
            i += 1
    return clean_args, stdout_handle, stderr_handle, stdout_handle_append, stderr_handle_append


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
        
        clean_args, stdout_handle, stderr_handle, stdout_handle_append, stderr_handle_append = extract_redirections(args)

        try:
            if stdout_handle_append == True:
                stdout = open(stdout_handle, "a") if stdout_handle else None
            else:
                stdout = open(stdout_handle, "w") if stdout_handle else None
            if stderr_handle_append == True:
                stderr = open(stderr_handle, "a") if stderr_handle else None
            else:
                stderr = open(stderr_handle, "w") if stderr_handle else None
            if command_name in BUILTINS:
                _run_cmd(command_name, clean_args, stdout=stdout, stderr=stderr)
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
