import sys


def main():
    while True:
        sys.stdout.write("$ ")
        pass
    # Wait for user input
        user_Input = input()
        if user_Input.strip() == "exit":
            break
        print(f"{user_Input}: command not found")

if __name__ == "__main__":
    main()
