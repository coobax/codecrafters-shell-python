import sys
import os
import subprocess

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
    Umbau in Klassen und Funktionen
    Parser in State Klasse
    Execution in eigener Funktion
    Builtins in eigene Funktionen
    Command Container
'''
def find_executable(exec_name):
    paths = os.environ.get("PATH", "").split(os.pathsep)
    for path in paths:
        full_path = os.path.join(path, exec_name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None

def sh_type(cmd_name):
    executable_path = find_executable(cmd_name)
    if cmd_name in BUILTINS:
        print(f"{cmd_name} is a shell builtin")
    elif executable_path is not None:
        print(f"{cmd_name} is {executable_path}")
    else:
        print(f"{cmd_name}: not found")

def sh_cd(*args):
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

def parse_line(line):
    esc_char = False
    in_single = False
    in_double = False
    tkn_active = False
    cur_tkn = []
    tokens = []

    for ch in line:
        if esc_char:
            cur_tkn.append(ch)
            esc_char = False
            tkn_active = True
            continue

        if ch == '\\':
            if not in_single and not in_double:
                esc_char = not esc_char
                if esc_char:
                    continue
            elif in_double:
                esc_char = True
                continue
                
        if ch == "'" and not in_double:
            tkn_active = True
            in_single = not in_single
        elif ch == '"' and not in_single:
            tkn_active = True
            in_double = not in_double
        elif ch.isspace() and not in_single and not in_double:
            if tkn_active:
                tokens.append("".join(cur_tkn))
                cur_tkn = []
                tkn_active = False
        else: 
            if not tkn_active:
                tkn_active = True
            cur_tkn.append(ch)

    if tkn_active:
        tokens.append("".join(cur_tkn))
    return tokens

BUILTINS = {
    "exit": lambda code=0, *_: sys.exit(int(code)),
    "echo": lambda *args: print(" ".join(args)),
    "type": sh_type,
    "pwd": lambda *args: print(os.getcwd()),
    "cd": sh_cd,
}

def main():
    while True:
        redirect_target = False
        sys.stdout.write("$ ")
        sys.stdout.flush()

        try:
            line = input()
            user_Input = parse_line(line)
        except EOFError:
            break

        if not user_Input:
            continue

        command_name = user_Input[0]

        args = user_Input[1:]

        if ">" in args:
            o = sys.stdout
            idx = args.index(">")
            out_name = args[idx + 1]

            # Redirect stdout to a file
            with open(out_name, 'w') as f:
                sys.stdout = f

            # Restore stdout
            #sys.stdout = o
            

        if command_name in BUILTINS:
            BUILTINS[command_name](*args)       
        else:
            resolved = find_executable(command_name)
            if resolved is None:
                print(f"{command_name}: command not found")
            else:
                try:
                    subprocess.run([command_name] + args, executable=resolved)
                except FileNotFoundError:
                    print(f"{command_name}: command not found")
                except PermissionError:
                    print(f"{command_name}: permission denied")
                except OSError as e:
                    print(f"Error executing {command_name}: {e}")

if __name__ == "__main__":
    main()
