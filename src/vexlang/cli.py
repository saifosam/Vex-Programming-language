import sys
from .parser import parse
from .interpreter import Interpreter


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: vex <file.vex>")
        raise SystemExit(1)

    path = argv[0]
    with open(path, encoding="utf-8") as f:
        source = f.read()

    ast_root = parse(source)
    interpreter = Interpreter(ast_root)
    interpreter.run()


if __name__ == "__main__":
    main()
