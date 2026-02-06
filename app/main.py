import sys
import os
import subprocess

def find_executable(exec_name):
    paths = os.environ.get("PATH", "").split(os.pathsep)
    for path in paths:
        full_path = os.path.join(path, exec_name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return

def sh_type(cmd_name):
    executable_path = find_executable(cmd_name)
    if cmd_name in BUILTINS:
        print(f"{cmd_name} is a shell builtin")
    elif executable_path is not None:
        print(f"{cmd_name} is {executable_path}")
    else:
        print(f"{cmd_name}: not found")

def sh_cd(*cd_path):
    if len(cd_path) == 0:
        cd_path = os.path.expanduser("~")
        os.chdir(cd_path)
    elif len(cd_path) == 1:
        try:
            cd_path = os.path.expanduser(cd_path[0])
            os.chdir(cd_path)
        except OSError:
            print(f"cd: {cd_path}: No such file or directory")
            return
    elif len(cd_path) > 1:
        print("cd: too many arguments")
        return

#No shlex for learning purposes, so we implement our own simple parser that handles single quotes and whitespace
def parse_line(line):
    in_single = False
    in_double = False
    tkn_active = False
    cur_tkn = []
    tokens = []
    for i in range(len(line)):
        if line[i] == "'" and not in_double:
            tkn_active = True
            in_single = not in_single
        elif line[i] == '"' and not in_single:
            tkn_active = True
            in_double = not in_double
        elif line[i].isspace() and not in_single and not in_double:
            if tkn_active:
                tokens.append("".join(cur_tkn))
                cur_tkn = []
                tkn_active = False
        else: 
            if not tkn_active:
                tkn_active = True
            cur_tkn.append(line[i])
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
        
        resolved = find_executable(command_name)

        if command_name in BUILTINS:
            BUILTINS[command_name](*args)       
        elif resolved is not None:
                subprocess.run([command_name] + args, executable=resolved)
        else:    
            print(f"{command_name}: command not found")

if __name__ == "__main__":
    main()
