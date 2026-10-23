"""The mark and the project glyphs, from src/house.json (exported from Secret Sauce's build.py, so they match the house SVGs)."""
import json
from . import SRC

HOUSE = SRC / "house.json"


def load():
    """-> {"MARK": [7 rows], "GLYPHS": {name: [5 rows]}}."""
    found = json.loads(HOUSE.read_text())
    missing = {"GLYPHS", "MARK"} - set(found)
    if missing:
        raise SystemExit(f"house.json: could not find {', '.join(sorted(missing))}")
    return found
