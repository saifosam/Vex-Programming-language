from style_parser import parse_style
from zones import split_zones
from .lexer import tokenize, Token, parse_literal


class ASTNode:
    def __init__(self, type, value=None, children=None, line=0):
        self.type = type
        self.value = value
        self.children = children or []
        self.line = line

    def __repr__(self):
        return f"ASTNode({self.type}, {self.value!r}, children={self.children}, line={self.line})"


def parse(source: str) -> ASTNode:
    """Parse a .vex source into an AST with top-level style, logic, and view nodes."""
    zones = split_zones(source)
    style_text = zones.get("style", "")
    logic_text = zones.get("logic", "")
    view_text = zones.get("view", "")

    style_ast = parse_style(style_text)
    view_ast = parse_view_tokens(view_text)

    root = ASTNode("Module", line=1)
    root.children.append(ASTNode("Style", value=style_ast, line=1))
    root.children.append(ASTNode("Logic", value=logic_text, line=1))
    root.children.append(ASTNode("View", value=view_ast, line=1))
    return root


def parse_view_tokens(view_text: str):
    tokens = list(tokenize(view_text))
    i = 0

    def peek():
        return tokens[i] if i < len(tokens) else Token("EOF", "", 0, 0)

    def advance():
        nonlocal i
        token = peek()
        i += 1
        return token

    def expect(expected_type):
        token = peek()
        if token.type != expected_type:
            raise SyntaxError(f"Expected {expected_type} on line {token.line}, got {token.type}")
        return advance()

    def is_keyword_argument():
        return peek().type == "NAME" and (i + 1) < len(tokens) and tokens[i + 1].type == "EQ"

    def parse_literal_value():
        token = peek()
        if token.type in {"STRING", "NUMBER", "NAME"}:
            return parse_literal(advance())
        raise SyntaxError(f"Unexpected literal token {token.type} on line {token.line}")

    def parse_args_kwargs():
        args = []
        kwargs = {}
        if peek().type == "RPAREN":
            return args, kwargs
        while True:
            if is_keyword_argument():
                key = advance().value
                advance()  # EQ
                kwargs[key] = parse_literal_value()
            else:
                args.append(parse_literal_value())
            if peek().type == "COMMA":
                advance()
                continue
            break
        return args, kwargs

    def parse_tag():
        name_token = expect("NAME")
        expect("LPAREN")
        args, kwargs = parse_args_kwargs()
        expect("RPAREN")
        children = []
        if peek().type == "COLON":
            advance()
            children = parse_block()
        return {"name": name_token.value, "args": args, "kwargs": kwargs, "children": children}

    def parse_block():
        if peek().type == "NEWLINE":
            advance()
        expect("INDENT")
        nodes = []
        while peek().type not in {"DEDENT", "EOF"}:
            if peek().type == "NEWLINE":
                advance()
                continue
            nodes.append(parse_statement())
        expect("DEDENT")
        return nodes

    def parse_statement():
        if peek().type == "NAME":
            node = parse_tag()
            if peek().type == "NEWLINE":
                advance()
            return node
        raise SyntaxError(f"Unexpected statement token {peek().type} on line {peek().line}")

    nodes = []
    while peek().type == "NEWLINE":
        advance()
    if peek().type == "INDENT":
        nodes = parse_block()
        return nodes
    while peek().type != "EOF":
        if peek().type == "NEWLINE":
            advance()
            continue
        nodes.append(parse_statement())
    return nodes
