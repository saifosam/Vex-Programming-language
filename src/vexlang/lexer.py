import ast
import re

TOKEN_SPECIFICATION = [
    ("STRING", r'"(?:\.|[^\"])*"|\'(?:\.|[^\'])*\''),
    ("NUMBER", r"\d+(?:\.\d+)?"),
    ("NAME", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("COLON", r":"),
    ("COMMA", r","),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("EQ", r"="),
    ("SKIP", r"[ \t]+"),
    ("MISMATCH", r"."),
]

TOKENS_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECIFICATION))

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}, {self.column})"


def tokenize(source):
    indent_stack = [0]
    line_no = 1
    for raw_line in source.splitlines(True):
        line = raw_line.rstrip("\r\n")
        if not line.strip() or line.lstrip().startswith("#"):
            line_no += 1
            continue

        indent = len(line) - len(line.lstrip(" "))
        if indent > indent_stack[-1]:
            indent_stack.append(indent)
            yield Token("INDENT", "", line_no, 0)
        else:
            while indent < indent_stack[-1]:
                indent_stack.pop()
                yield Token("DEDENT", "", line_no, 0)
            if indent != indent_stack[-1]:
                raise IndentationError(
                    f"Inconsistent indentation on line {line_no}: {indent} spaces"
                )

        pos = indent
        while pos < len(line):
            mo = TOKENS_RE.match(line, pos)
            if not mo:
                raise SyntaxError(f"Unexpected character on line {line_no}: {line[pos]!r}")
            kind = mo.lastgroup
            value = mo.group(kind)
            pos = mo.end()
            if kind == "SKIP":
                continue
            if kind == "MISMATCH":
                raise SyntaxError(f"Unexpected character {value!r} on line {line_no}")
            yield Token(kind, value, line_no, pos)

        yield Token("NEWLINE", "", line_no, pos)
        line_no += 1

    while len(indent_stack) > 1:
        indent_stack.pop()
        yield Token("DEDENT", "", line_no, 0)
    yield Token("EOF", "", line_no, 0)


def parse_literal(token):
    if token.type == "STRING":
        return ast.literal_eval(token.value)
    if token.type == "NUMBER":
        return ast.literal_eval(token.value)
    if token.type == "NAME":
        return token.value
    raise SyntaxError(f"Unexpected literal token {token.type} on line {token.line}")
