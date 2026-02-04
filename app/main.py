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

    # Read input; exit cleanly on EOF (Ctrl+D / input stream ended)
        try:
            user_Input = input().split()
        except EOFError:
            break
        
        # Ignore empty lines (just pressing Enter)
        if not user_Input:
            continue

        command_name = user_Input[0]

        args = user_Input[1:]
        
        resolved = find_executable(command_name)

        if command_name in BUILTINS:
            BUILTINS[command_name](*args)       
        elif resolved is not None:
                # Run the resolved executable, but keep argv[0] as the original command name
                subprocess.run([command_name] + args, executable=resolved)
        else:    
            print(f"{command_name}: command not found")

if __name__ == "__main__":
    main()
