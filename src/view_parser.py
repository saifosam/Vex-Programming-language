"""Parse the ``view:`` zone of a .vex file into a tree of node dicts."""

from __future__ import annotations

import ast
import textwrap
from typing import Any

from errors import VexError

# ---------------------------------------------------------------------------
# Type alias for a parsed view node
# ---------------------------------------------------------------------------
ViewNode = dict[str, Any]
"""
A node in the parsed view tree with keys:

- ``name`` — tag name (e.g. ``"card"``, ``"button"``)
- ``args`` — positional string arguments
- ``kwargs`` — keyword arguments (strings, ints, or name references)
- ``children`` — list of child ``ViewNode`` dicts
"""


def _parse_call_str(call_str: str, line_no: int) -> ViewNode:
    """Parse a single view call like ``button("Click", onclick=fn)`` into a ViewNode.

    Uses Python's ``ast`` module to safely evaluate the call syntax.
    Keyword values that are bare names (e.g. ``onclick=increment``) are
    stored as strings rather than evaluated.
    """
    if "(" not in call_str:
        call_str += "()"
    try:
        tree = ast.parse(call_str)
        call = tree.body[0].value
    except (SyntaxError, IndexError, AttributeError):
        raise VexError(f"Could not understand '{call_str}'.", line=line_no)

    name = call.func.id

    args = [ast.literal_eval(a) for a in call.args]
    kwargs: dict[str, Any] = {}
    for kw in call.keywords:
        if isinstance(kw.value, ast.Name):
            kwargs[kw.arg] = kw.value.id
        else:
            kwargs[kw.arg] = ast.literal_eval(kw.value)

    return {"name": name, "args": args, "kwargs": kwargs, "children": []}


def parse_view(view_text: str) -> list[ViewNode]:
    """Parse the ``view:`` zone text into a list of root-level ViewNodes.

    Indentation defines parent-child relationships:

    - A line ending with ``:`` is a container; subsequent indented lines
      become its children.
    - A line without a trailing ``:`` is a leaf node.

    Returns:
        A flat list of root-level ``ViewNode`` dicts (containers hold
        their children in the ``"children"`` list).
    """
    view_text = textwrap.dedent(view_text)
    lines = [(i + 1, line) for i, line in enumerate(view_text.split("\n")) if line.strip() != ""]

    root: list[ViewNode] = []
    stack: list[tuple[int, list[ViewNode]]] = [(-1, root)]

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