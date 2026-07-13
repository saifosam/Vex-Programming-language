from src.view_parser import parse_view

def test_basic_view():
    sample = """    text("Count is 0")
    button("Click me", onclick=increment)
"""
    result = parse_view(sample)
    assert result == [
        {"name": "text", "args": ["Count is 0"], "kwargs": {}, "children": []},
        {"name": "button", "args": ["Click me"], "kwargs": {"onclick": "increment"}, "children": []},
    ]

def test_nested_containers():
    sample = """    card(background="black"):
        text("Saif", role="title")
        button("Click", onclick=increment)
"""
    result = parse_view(sample)
    assert len(result) == 1
    assert result[0]["name"] == "card"
    assert result[0]["kwargs"] == {"background": "black"}
    assert len(result[0]["children"]) == 2
    assert result[0]["children"][0]["name"] == "text"
    assert result[0]["children"][1]["name"] == "button"