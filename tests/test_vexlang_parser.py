from vexlang.lexer import tokenize
from vexlang.parser import parse


def test_tokenize_view_indentation():
    source = """view:
    card():
        text("Hello", role="title")
"""
    tokens = [t.type for t in tokenize(source)]
    assert 'INDENT' in tokens
    assert 'DEDENT' in tokens
    assert 'EOF' in tokens


def test_parse_view_nested_block():
    source = """view:
    card():
        text("Hello", role="title")
"""
    ast = parse(source)
    assert ast.type == 'Module'
    view = ast.children[2].value
    assert isinstance(view, list)
    assert view[0]['name'] == 'card'
    assert view[0]['children'][0]['name'] == 'text'
    assert view[0]['children'][0]['kwargs']['role'] == 'title'
