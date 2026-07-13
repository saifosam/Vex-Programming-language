import ast
import textwrap
import difflib
from src.errors import VexError


def _parse_call_str(call_str, line_no):
    if "(" not in call_str:
        call_str += "()"
    try:
        tree = ast.parse(call_str)
        call = tree.body[0].value
    except (SyntaxError, IndexError, AttributeError):
        raise VexError(f"Could not understand '{call_str}'.", line=line_no)

    name = call.func.id

    args = [ast.literal_eval(a) for a in call.args]
    kwargs = {}
    for kw in call.keywords:
        if isinstance(kw.value, ast.Name):
            kwargs[kw.arg] = kw.value.id
        else:
            kwargs[kw.arg] = ast.literal_eval(kw.value)

    return {"name": name, "args": args, "kwargs": kwargs, "children": []}


def parse_view(view_text: str) -> list:
    view_text = textwrap.dedent(view_text)
    lines = [(i + 1, line) for i, line in enumerate(view_text.split("\n")) if line.strip() != ""]

    root = []
    stack = [(-1, root)]  # (indent_level, children_list_it_owns)

    for line_no, raw_line in lines:
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        content = raw_line.strip()

        while indent <= stack[-1][0]:
            stack.pop()

        parent_children = stack[-1][1]
        is_container = content.endswith(":")
        call_str = content[:-1] if is_container else content

        node = _parse_call_str(call_str, line_no)
        parent_children.append(node)

        if is_container:
            stack.append((indent, node["children"]))

    return root