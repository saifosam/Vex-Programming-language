import ast

def test_logic_zone_execs_as_python():
    code = "count = 0\ndef greet():\n    return 'hi'\n"
    tree = ast.parse(code)
    compiled = compile(tree, "<logic>", "exec")
    namespace = {}
    exec(compiled, namespace)

    assert namespace["count"] == 0
    assert namespace["greet"]() == "hi"