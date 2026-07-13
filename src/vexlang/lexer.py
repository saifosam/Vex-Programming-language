import re

TOKEN_SPECIFICATION = [
    ("NUMBER", r"\d+(?:\.\d+)?"),
    ("STRING", r'"(?:\\.|[^\\"])*"|\'(?:\\.|[^\\'])*\''),
    ("NAME", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("COLON", r":"),
    ("COMMA", r","),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("EQ", r"="),
    ("NEWLINE", r"\n"),
    ("INDENT", r"[ ]+"),
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
    line_num = 1
    line_start = 0
    for mo in TOKENS_RE.finditer(source):
        kind = mo.lastgroup
        value = mo.group(kind)
        column = mo.start() - line_start
        if kind == "NEWLINE":
            line_num += 1
            line_start = mo.end()
            yield Token(kind, value, line_num, column)
        elif kind == "SKIP":
            continue
        elif kind == "MISMATCH":
            raise SyntaxError(f"Unexpected character {value!r} on line {line_num}")
        else:
            yield Token(kind, value, line_num, column)
