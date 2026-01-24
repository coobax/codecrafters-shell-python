import sys

BUILTINS = {
    "exit": lambda code=0, *_: sys.exit(int(code)),
    "echo": lambda *args: print(" ".join(args)),
    "type": lambda x: (
        print(f"{x} is a shell builtin") if x in BUILTINS else print(f"{x}: not found")
    ),
}

def main():
    while True:
        sys.stdout.write("$ ")

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
