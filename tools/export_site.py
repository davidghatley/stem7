"""Write docs/data/glyphs.json for the website: every glyph's cells, bearings, code points and note, per style,
plus a few round-0 drawings (tools/round0.json) for the before/after figure.

    python tools/export_site.py
"""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s7lib import ROOT
from s7lib.fontbuild import sources, bold_set
from s7lib.boldrule import embolden


def pack(gs):
    out = []
    for name, g in gs.items():
        if not g.cps:
            continue
        out.append({"n": name, "u": [f"{c:04X}" for c in g.cps], "r": g.rows or [], "l": g.lsb, "rs": g.rsb,
                    "w": g.width, "t": g.tabular, "note": "\n".join(l.strip() for l in g.note).strip()})
    return out


def kerns(style):
    """kern-<style>.txt expanded to {"F a": [-1, mean gap], ...} in cells; the first rule for a pair wins, as in the font."""
    classes, out = {}, {}
    for raw in (ROOT / "src" / f"kern-{style}.txt").read_text().splitlines():
        p = raw.split("#", 1)[0].split()
        mean = re.search(r"mean ([0-9.]+)", raw)
        if p and p[0] == "class":
            classes[p[1]] = p[3:]
        elif p and p[0] == "kern":
            for a in classes.get(p[1], [p[1]]):
                for c in classes.get(p[2], [p[2]]):
                    out.setdefault(f"{a} {c}", [int(p[3]), float(mean[1]) if mean else None])
    return out


reg, bold = sources()
b, _ = bold_set(reg, bold)
# the auto-bold draft of every glyph that was then redrawn by hand
drafts = {n: embolden(g).rows for n, g in reg.items() if g.rows and not g.source and not g.liga
          and n in b and embolden(g).rows != b[n].rows}
data = {"regular": pack(reg), "bold": pack(b), "round0": json.loads((ROOT / "tools" / "round0.json").read_text()),
        "drafts": drafts, "kern": kerns("regular")}
p = ROOT / "site" / "data" / "glyphs.json"
p.write_text(json.dumps(data, separators=(",", ":")))
print(p.relative_to(ROOT), len(data["regular"]), "regular,", len(data["bold"]), "bold,", p.stat().st_size, "B")
