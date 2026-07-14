import importlib.util
import pytest

from vexlang.parser import parse
from vexlang.interpreter import Interpreter
from vexlang.errors import VexError


def customtkinter_available():
    return importlib.util.find_spec('customtkinter') is not None


def test_parse_vex_zones():
    source = """style:
    button:
        color: blue

logic:
    count = 0

view:
    text("Hello")
"""
    ast = parse(source)
    assert ast.type == 'Module'
    assert ast.children[0].type == 'Style'
    assert ast.children[1].type == 'Logic'
    assert ast.children[2].type == 'View'


@pytest.mark.skipif(not customtkinter_available(), reason='customtkinter not installed')
def test_interpreter_runs_logic_and_parses_view():
    source = """style:
    button:
        color: blue

logic:
    x = 1

view:
    text("Hello")
"""
    ast = parse(source)
    interpreter = Interpreter(ast)
    interpreter.run()
