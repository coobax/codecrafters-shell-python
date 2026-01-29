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
}

def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

    # Wait for user input
        user_Input = input().split()

        command_name = user_Input[0]

        args = user_Input[1:]
        
        if command_name in BUILTINS:
            BUILTINS[command_name](*args)
        
        elif find_executable(command_name):
            try:
                subprocess.run([command_name] + args)
            except Exception as e:
                print(f"Error executing {command_name}: {e}")
        else:    
            print(f"{command_name}: command not found")

if __name__ == "__main__":
    main()
