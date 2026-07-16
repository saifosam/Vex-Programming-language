"""Parse the ``style:`` zone of a .vex file into a selector dictionary."""

from __future__ import annotations

import textwrap


def parse_style(style_text: str) -> dict[str, dict[str, str]]:
    """
    Parse a style zone string into a nested dictionary of selectors.

    Each top-level block like::

        window:
            title: My App
            width: 380

    becomes ``{"window": {"title": "My App", "width": "380"}}``.

    Returns:
        A dict mapping each selector name to its key-value properties.
    """
    style_text = textwrap.dedent(style_text)
    result: dict[str, dict[str, str]] = {}
    current_selector: str | None = None

    for line in style_text.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.endswith(":") and ":" not in stripped[:-1]:
            current_selector = stripped[:-1]
            result[current_selector] = {}
        else:
            key, value = stripped.split(":", 1)
            clean_value = value.strip().strip('"').strip("'")
            if current_selector is not None:
                result[current_selector][key.strip()] = clean_value

    return result