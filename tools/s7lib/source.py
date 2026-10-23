"""The .s7 glyph source format: plain text, one block per glyph, rows of X (ink) and . (paper).

    # Comment lines directly above a block are kept as the glyph's note.
    glyph A U+0041
    XXXXX   # cap
    X...X
    X...X
    XXXXX   # x-height
    X...X
    X...X
    X...X   # baseline
    .....
    .....   # descender

Every drawn glyph has exactly 9 rows: rows 1-7 sit above the baseline (row 1 is the cap line, row 4 the
x-height line, row 7 rests on the baseline) and rows 8-9 are the descender. Everything after `#` on a row
is a comment. Widths are free; every row of a glyph must be the same width.

Header: `glyph <name> <U+XXXX[,U+YYYY]|-> [key=value ...] [flag ...]`
    lsb=0 rsb=1    side bearings in whole cells (defaults 0 and 1)
    width=3        an empty glyph (space) with this advance in cells; no rows
    from=MARK      rows come from house.json's MARK (7x7, on the baseline); no rows in the file
    from=GLYPHS.x  rows come from house.json's GLYPHS["x"] (5x5, on the baseline); no rows in the file
    liga=d+h       this glyph is the ligature of those glyphs (by name)
    tabular        a figure: every tabular glyph in a style has the same width
    allow=a,b      lint exceptions this drawing needs on purpose (block, thin, offaxis, dup), kept next to it
"""
import re
from dataclasses import dataclass, field

ROWS, CAP_ROW, X_ROW, BASE_ROW = 9, 0, 3, 6      # row indices: cap line, x-height line, last row above baseline
CAP, XH, DESC = 7, 4, 2                         # in cells
GUIDES = {0: "cap", 3: "x-height", 6: "baseline", 8: "descender"}
HEAD = re.compile(r"^glyph\s+(\S+)\s+(\S+)(.*)$")
ROW = re.compile(r"^[X.]+$")


@dataclass
class Glyph:
    name: str
    cps: list
    rows: list = None
    lsb: int = 0
    rsb: int = 1
    width: int = None          # advance for empty glyphs
    source: str = None         # from=
    liga: list = None
    tabular: bool = False
    allow: list = field(default_factory=list)
    note: list = field(default_factory=list)
    line: int = 0
    file: str = ""

    @property
    def w(self):
        return len(self.rows[0]) if self.rows else 0

    @property
    def advance(self):
        return self.width if self.width is not None else self.lsb + self.w + self.rsb

    def ink(self):
        return {(c, r) for r, row in enumerate(self.rows or []) for c, ch in enumerate(row) if ch == "X"}

    def header(self):
        cps = ",".join(f"U+{c:04X}" for c in self.cps) if self.cps else "-"
        opts = []
        if self.width is not None: opts.append(f"width={self.width}")
        if self.source: opts.append(f"from={self.source}")
        if self.liga: opts.append("liga=" + "+".join(self.liga))
        if self.lsb != 0: opts.append(f"lsb={self.lsb}")
        if self.rsb != 1: opts.append(f"rsb={self.rsb}")
        if self.tabular: opts.append("tabular")
        if self.allow: opts.append("allow=" + ",".join(self.allow))
        return " ".join([f"glyph {self.name} {cps}"] + opts)


class SourceError(Exception):
    pass


def place_house(src, house):
    """Rows for from=MARK / from=GLYPHS.name, seated on the baseline."""
    if src == "MARK":
        art = house["MARK"]
    elif src.startswith("GLYPHS."):
        art = house["GLYPHS"][src.split(".", 1)[1]]
    else:
        raise SourceError(f"unknown from={src}")
    w = len(art[0])
    blank = "." * w
    top = CAP - len(art)
    return [blank] * top + list(art) + [blank] * DESC


def parse(path, house=None):
    """-> ordered {name: Glyph}. Raises SourceError with file:line on any malformed block."""
    text = pathlib_read(path)
    glyphs, cur, note = {}, None, []

    def close():
        nonlocal cur
        if cur is None:
            return
        if cur.source:
            if cur.rows:
                raise SourceError(f"{path}:{cur.line}: {cur.name} has from= and drawn rows")
            if house is None:
                raise SourceError(f"{path}:{cur.line}: {cur.name} needs src/house.json (from={cur.source})")
            cur.rows = place_house(cur.source, house)
        elif cur.width is not None:
            if cur.rows:
                raise SourceError(f"{path}:{cur.line}: {cur.name} has width= and drawn rows")
        else:
            if len(cur.rows) != ROWS:
                raise SourceError(f"{path}:{cur.line}: {cur.name} has {len(cur.rows)} rows, needs {ROWS}")
            widths = {len(r) for r in cur.rows}
            if len(widths) != 1:
                raise SourceError(f"{path}:{cur.line}: {cur.name} has ragged rows (widths {sorted(widths)})")
        if cur.name in glyphs:
            raise SourceError(f"{path}:{cur.line}: duplicate glyph {cur.name}")
        glyphs[cur.name] = cur
        cur = None

    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        bare = line.split("#", 1)[0].strip()
        if not bare:
            if line.strip().startswith("#") and cur is None:
                note.append(line.strip()[1:].strip())
            elif not line.strip():
                close()
                note = [] if cur is None else note
            continue
        m = HEAD.match(bare)
        if m:
            close()
            name, cps, rest = m.groups()
            g = Glyph(name=name, cps=[] if cps == "-" else [int(c[2:], 16) for c in cps.split(",")],
                      rows=[], line=n, file=str(path), note=note)
            note = []
            for tok in rest.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    if k in ("lsb", "rsb", "width"): setattr(g, k, int(v))
                    elif k == "from": g.source = v
                    elif k == "liga": g.liga = v.split("+")
                    elif k == "allow": g.allow = v.split(",")
                    else: raise SourceError(f"{path}:{n}: unknown option {k}")
                elif tok == "tabular":
                    g.tabular = True
                else:
                    raise SourceError(f"{path}:{n}: unknown flag {tok}")
            cur = g
            continue
        if cur is None:
            raise SourceError(f"{path}:{n}: row outside a glyph block: {bare!r}")
        if not ROW.match(bare):
            raise SourceError(f"{path}:{n}: {cur.name}: row must be X and . only: {bare!r}")
        cur.rows.append(bare)
    close()
    return glyphs


def pathlib_read(path):
    import pathlib
    return pathlib.Path(path).read_text()


def dump_glyph(g):
    out = [f"# {t}" if t else "#" for t in g.note]
    out.append(g.header())
    if g.source or g.width is not None:
        return "\n".join(out)
    pad = max(g.w, 1) + 3
    for i, r in enumerate(g.rows):
        out.append(f"{r:<{pad}}# {GUIDES[i]}" if i in GUIDES else r)
    return "\n".join(out)


def dump(glyphs, preamble=""):
    body = "\n\n".join(dump_glyph(g) for g in glyphs.values())
    return (preamble.rstrip() + "\n\n" if preamble else "") + body + "\n"
