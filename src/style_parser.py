import textwrap

def parse_style(style_text: str) -> dict:
    style_text = textwrap.dedent(style_text)  # removes shared leading whitespace
    result = {}
    current_selector = None

    for line in style_text.splitlines():
        stripped = line.strip()

        if stripped == "":
            continue

        if stripped.endswith(":") and ":" not in stripped[:-1]:
            current_selector = stripped[:-1]
            result[current_selector] = {}
        else:
            key, value = stripped.split(":", 1)
            clean_value = value.strip().strip('"').strip("'")
            result[current_selector][key.strip()] = clean_value

    return result