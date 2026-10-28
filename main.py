import sys

from src.repl import run_file, start


def main(argv: list[str]) -> int:
    if len(argv) == 1:
        start()
        return 0
    if len(argv) == 2:
        return run_file(argv[1])
    print("uso: python main.py [archivo.ssg]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
