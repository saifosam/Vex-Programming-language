# src/zones.py
def split_zones(source: str) -> dict[str, str]:
    """
    Splits a .beam file into its top-level zones based on
    lines that start at column 0 and end with ':'.
    Returns {"style": "...", "logic": "...", "view": "..."}
    """
    zones = {"style": "", "logic": "", "view": ""}
    current = None
    for line in source.splitlines():
        stripped = line.strip()
        if stripped in ("style:", "logic:", "view:"):
            current = stripped[:-1]
            continue
        if current:
            zones[current] += line + "\n"
    return zones

    