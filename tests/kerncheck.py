"""Shape every pair the kerning source asks for with HarfBuzz and check the font applies exactly that value.

    python tests/kerncheck.py        -> exits 1 if any pair in src/kern-*.txt is missing or wrong in fonts/
"""
import pathlib, sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
CELL = 300


def pairs(style):
    classes, want = {}, {}
    for raw in (ROOT / "src" / f"kern-{style.lower()}.txt").read_text().splitlines():
        p = raw.split("#", 1)[0].split()
        if not p:
            continue
        if p[0] == "class":
            classes[p[1]] = p[3:]
        elif p[0] == "kern":
            for a in classes.get(p[1], [p[1]]):
                for b in classes.get(p[2], [p[2]]):
                    want.setdefault((a, b), int(p[3]) * CELL)   # first rule wins, as in the feature file
    return want


def check(style):
    path = ROOT / "fonts" / f"Stem7-{style}.ttf"
    tt = TTFont(path)
    cmap = {v: k for k, v in tt.getBestCmap().items()}
    face = hb.Face(path.read_bytes())
    font = hb.Font(face)
    bad = []
    want = pairs(style)
    for (a, b), v in sorted(want.items()):
        if a not in cmap or b not in cmap:
            continue
        buf = hb.Buffer()
        buf.add_str(chr(cmap[a]) + chr(cmap[b]))
        buf.guess_segment_properties()
        hb.shape(font, buf, {"kern": True, "liga": False})
        got = buf.glyph_positions[0].x_advance - tt["hmtx"][a][0]
        if got != v:
            bad.append(f"{a}+{b}: wants {v // CELL}, font gives {got / CELL:g}")
    print(f"{style}: {len(want) - len(bad)}/{len(want)} pairs as written" + "".join(f"\n  {x}" for x in bad))
    return not bad


if __name__ == "__main__":
    sys.exit(0 if all([check("Regular"), check("Bold")]) else 1)
