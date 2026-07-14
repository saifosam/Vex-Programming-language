import sys
import textwrap
from zones import split_zones
from style_parser import parse_style
from view_parser import parse_view
from codegen import generate_app
from errors import VexError

def main():
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        source = f.read()

    try:
        zones = split_zones(source)

        logic_code = textwrap.dedent(zones["logic"])
        namespace = {}
        exec(compile(logic_code, "<logic>", "exec"), namespace)

        style = parse_style(zones["style"])
        view = parse_view(zones["view"])

        app = generate_app(style, view, namespace)
        app.mainloop()

    except SyntaxError as e:
        print(f"Syntax error in {path}, line {e.lineno}: {e.msg}")
        sys.exit(1)

    except VexError as e:
        print(f"{path}: {e.display()}")
        sys.exit(1)

if __name__ == "__main__":
    main()