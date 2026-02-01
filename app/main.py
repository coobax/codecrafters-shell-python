import sys
import os
import subprocess

def find_executable(cmd):
    paths = os.environ.get("PATH", "").split(os.pathsep)
    for path in paths:
        full_path = os.path.join(path, cmd)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None

def sh_type(cmd):
    executable_path = find_executable(cmd)
    if cmd in BUILTINS:
        print(f"{cmd} is a shell builtin")
    elif executable_path is not None:
        print(f"{cmd} is {executable_path}")
    else:
        print(f"{cmd}: not found")

BUILTINS = {
    "exit": lambda code=0, *_: sys.exit(int(code)),
    "echo": lambda *args: print(" ".join(args)),
    "type": sh_type,
    "pwd": lambda *args: print(os.getcwd()),
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
