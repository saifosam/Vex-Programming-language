from style_parser import parse_style

def test_single_selector():
    sample = """    button:
        color: blue
        size: 14
"""
    result = parse_style(sample)
    assert result == {"button": {"color": "blue", "size": "14"}}

def test_multiple_selectors():
    sample = """    button:
        color: blue
        size: 14
    title:
        color: red
"""
    result = parse_style(sample)
    assert result == {
        "button": {"color": "blue", "size": "14"},
        "title": {"color": "red"},
    }
def test_quoted_values_are_unquoted():
    sample = '''    window:
        background: "#eef1f6"
'''
    result = parse_style(sample)
    assert result == {"window": {"background": "#eef1f6"}}