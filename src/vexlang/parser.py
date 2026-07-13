from .lexer import tokenize, Token

class ASTNode:
    def __init__(self, type, value=None, children=None, line=0):
        self.type = type
        self.value = value
        self.children = children or []
        self.line = line

    def __repr__(self):
        return f"ASTNode({self.type}, {self.value!r}, children={self.children}, line={self.line})"


def parse(source):
    tokens = list(tokenize(source))
    root = ASTNode("Module", line=1)
    i = 0

    def peek():
        return tokens[i] if i < len(tokens) else Token("EOF", "", 0, 0)

    def advance():
        nonlocal i
        token = peek()
        i += 1
        return token

    def expect(type):
        token = peek()
        if token.type != type:
            raise SyntaxError(f"Expected {type} at line {token.line}, got {token.type}")
        return advance()

    while peek().type != "EOF":
        token = peek()
        if token.type == "NAME" and token.value in {"style", "logic", "view"}:
            advance()
            expect("COLON")
            section = token.value
            content = []
            while peek().type not in {"EOF", "NAME"}:
                content.append(advance())
            root.children.append(ASTNode(section, value=content, line=token.line))
        else:
            raise SyntaxError(f"Unexpected token {token.value!r} on line {token.line}")

    return root
