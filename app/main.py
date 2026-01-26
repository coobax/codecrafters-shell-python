import sys
import os

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

        cmd = user_Input[0]

        args = user_Input[1:]
        
        if cmd in BUILTINS:
            BUILTINS[cmd](*args)
            
        else:    
            print(f"{cmd}: command not found")

if __name__ == "__main__":
    main()
