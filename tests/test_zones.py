from src.zones import split_zones

def test_basic_split():
    source = """style:
    button:
        color: blue

logic:
    count = 0

view:
    text("hello")
"""
    result = split_zones(source)

    assert "button" in result["style"]
    assert "count = 0" in result["logic"]
    assert "text(\"hello\")" in result["view"]