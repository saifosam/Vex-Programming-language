"""Split a .vex file into its top-level style/logic/view zones."""

from __future__ import annotations


def split_zones(source: str) -> dict[str, str]:
    """
    Split a .vex source string into its three top-level zones.

    Zones are identified by lines that start with ``style:``, ``logic:``,
    or ``view:`` at column 0. Everything after a zone header until the next
    zone header (or end of file) belongs to that zone.

    Returns:
        A dict with keys ``"style"``, ``"logic"``, ``"view"``, each
        mapped to the raw text of that zone (empty string if absent).
    """
    zones: dict[str, str] = {"style": "", "logic": "", "view": ""}
    current: str | None = None
    for line in source.splitlines():
        stripped = line.strip()
        if stripped in ("style:", "logic:", "view:"):
            current = stripped[:-1]
            continue
        if current:
            zones[current] += line + "\n"
    return zones
