"""lint: glyph checks for Stem 7. Errors fail the run; warnings are printed (and fail with --strict).

Source checks (Regular and Bold):
  lines      caps and figures span the cap line to the baseline; lowercase sits on the baseline and reaches
             the x-height, the ascender (cap line) or, for i and j, the dot row; descenders reach row 9;
             the mark and pantry glyphs stand on the baseline
  axis       operators, dashes, arrows and the middle dot centre on row 4, the mark's bar row
  stems      Regular: no 2x2 block of ink (a stroke two cells thick); Bold: no ink run one cell wide
             (verticals and diagonal steps are two cells; horizontals stay one cell tall)
  bearings   ink touches the first and last column (spacing lives in lsb/rsb, not blank columns), lsb 0..1,
             rsb 1 (0 only for a glyph that joins, 2 at most); tabular figures share one width
  charset    everything the house sets (REQUIRED below) is mapped
  dups       no two mapped glyphs share a drawing; confusable sets differ by 2+ cells
  liga       each ligature's parts exist, and the ligature is exactly its parts sharing one stem
Font checks (fonts/*.ttf): every outline point, advance and kern on the 300-unit cell grid (Grid: the cell
grid plus its gap), metrics as documented, name table and licence present, PUA and liga present.
Exceptions a drawing needs on purpose are written next to it in the source: `allow=block,offaxis`.
"""
import itertools
from fontTools.ttLib import TTFont
from . import OUT
from .source import SourceError
from .fontbuild import sources, bold_set, CELL, UPM, ASC, DSC, GRID_GAP, VERSION

REQUIRED = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ" "abcdefghijklmnopqrstuvwxyz" "0123456789"
            " .,:;!?'\"-_()[]{}/\\|+=*#%&@$<>^~`"
            " ·×•°→←↑↓↗–—’‘“”… "
            + "".join(chr(0xE000 + i) for i in range(8)))
ASCENDERS, DOTTED, DESCENDERS = set("bdfhkl"), set("ijt"), set("gjpqy")  # t starts on row 2, like the dots
AXIS = {"hyphen", "endash", "emdash", "periodcentered", "bullet", "plus", "multiply", "equal", "less", "greater",
        "arrowright", "arrowleft", "uni2197", "asterisk", "asciitilde"}
CONFUSABLE = [("O", "zero"), ("O", "o"), ("I", "l", "one", "bar", "i"), ("S", "five"), ("B", "eight"), ("Z", "two"),
              ("G", "six"), ("a", "o"), ("g", "q"), ("g", "nine"), ("D", "O"), ("u", "v"), ("x", "multiply"),
              ("quotesingle", "quoteright"), ("comma", "quoteright")]


class Report:
    def __init__(self):
        self.err, self.warn = [], []

    def e(self, style, g, msg):
        self.err.append(f"ERROR {style:7} {g:16} {msg}")

    def w(self, style, g, msg):
        self.warn.append(f"warn  {style:7} {g:16} {msg}")


def ink_rows(g):
    rs = [r for r, row in enumerate(g.rows) if "X" in row]
    return (rs[0], rs[-1]) if rs else (None, None)


def check_lines(st, g, R):
    top, bot = ink_rows(g)
    if top is None:
        return
    ch = chr(g.cps[0]) if g.cps else ""
    if g.source:
        if bot != 6:
            R.e(st, g.name, f"house glyph must stand on the baseline (bottom row {bot + 1})")
        return
    if ch.isascii() and (ch.isupper() or ch.isdigit()):
        if (top, bot) != (0, 6):
            R.e(st, g.name, f"cap/figure spans rows {top + 1}-{bot + 1}, must be 1-7")
    elif ch.isascii() and ch.islower():
        want_top = 0 if ch in ASCENDERS else ((0, 1) if ch in DOTTED else 3)  # Bold's 2x2 dot starts on row 1
        want_bot = 8 if ch in DESCENDERS else 6
        if top not in (want_top if isinstance(want_top, tuple) else (want_top,)):
            R.e(st, g.name, f"top row {top + 1}, expected row {want_top + 1 if isinstance(want_top, int) else want_top[-1] + 1}")
        if bot != want_bot:
            R.e(st, g.name, f"bottom row {bot + 1}, expected {want_bot + 1}")
    if g.name in AXIS and "offaxis" not in g.allow:
        if (top + bot) / 2 != 3:
            R.e(st, g.name, f"centre is row {(top + bot) / 2 + 1:g}, operators centre on row 4 (allow=offaxis to waive)")


def blocks(g):
    ink = g.ink()
    return sorted((c, r) for (c, r) in ink if {(c + 1, r), (c, r + 1), (c + 1, r + 1)} <= ink)


def thin_stems(g):
    """Bold: ink cells with no ink to their left or right. Every vertical or diagonal stroke in Bold is
    two cells wide, so a horizontal run of one cell is a thin spot (a Regular stroke left in the Bold)."""
    ink = g.ink()
    return sorted((c, r) for (c, r) in ink if (c - 1, r) not in ink and (c + 1, r) not in ink)


def check_stems(st, g, R):
    if g.source or not g.rows:
        return
    if st == "Regular" and "block" not in g.allow:
        b = blocks(g)
        if b:
            R.e(st, g.name, f"2x2 block of ink at {cells(b)}: a 2-cell stroke in Regular (allow=block to waive)")
    if st == "Bold" and "thin" not in g.allow:
        t = thin_stems(g)
        if t:
            R.e(st, g.name, f"1-cell vertical stroke at {cells(t)}: Bold stems are 2 cells (allow=thin to waive)")


def cells(lst):
    return " ".join(f"c{c + 1}r{r + 1}" for c, r in lst[:4]) + (" ..." if len(lst) > 4 else "")


def check_bearings(st, g, R):
    if not g.rows or g.source:
        return
    ink_cols = [c for c in range(g.w) if any(row[c] == "X" for row in g.rows)]
    if not ink_cols:
        return
    if not g.tabular and (ink_cols[0] != 0 or ink_cols[-1] != g.w - 1):
        R.e(st, g.name, "blank columns inside the drawing: trim them and use lsb/rsb")
    if g.lsb not in (0, 1):
        R.w(st, g.name, f"lsb {g.lsb}")
    if g.rsb not in (0, 1, 2) or (g.rsb != 1 and not g.note):
        R.w(st, g.name, f"rsb {g.rsb} without a note saying why")


def check_tabular(st, glyphs, R):
    tab = [g for g in glyphs.values() if g.tabular]
    widths = {g.advance for g in tab}
    if len(widths) > 1:
        R.e(st, "figures", f"tabular advances differ: {sorted(widths)}")
    fs = glyphs.get("figurespace")
    if fs and widths and fs.advance not in widths:
        R.e(st, "figurespace", f"advance {fs.advance} != figure advance {sorted(widths)}")
    for g in tab:
        cols = [c for c in range(g.w) if any(row[c] == "X" for row in g.rows)]
        left, right = cols[0], g.w - 1 - cols[-1]
        if abs(left - right) > 1:
            R.w(st, g.name, f"figure sits off-centre in its tabular box ({left} | {right})")


def check_charset(st, glyphs, R):
    have = {cp for g in glyphs.values() for cp in g.cps}
    missing = [c for c in REQUIRED if ord(c) not in have]
    if missing:
        R.e(st, "charset", "missing " + " ".join(f"U+{ord(c):04X}" for c in missing))


def check_dups(st, glyphs, R):
    seen = {}
    for g in glyphs.values():
        if not g.rows or not g.cps or not any(g.ink()) or "dup" in g.allow:
            continue
        key = tuple(g.rows)
        if key in seen:
            R.e(st, g.name, f"same drawing as {seen[key]}")
        seen.setdefault(key, g.name)
    for group in CONFUSABLE:
        for a, b in itertools.combinations(group, 2):
            ga, gb = glyphs.get(a), glyphs.get(b)
            if not ga or not gb or not ga.rows or not gb.rows:
                continue
            if ga.w == gb.w and ga.lsb == gb.lsb:
                d = len(ga.ink() ^ gb.ink())
                if d < 2:
                    R.e(st, f"{a}/{b}", f"confusable: differ by {d} cell")
                elif d < 4:
                    R.w(st, f"{a}/{b}", f"confusable: differ by only {d} cells")


def check_liga(st, glyphs, R):
    for g in glyphs.values():
        if not g.liga:
            continue
        parts = [glyphs.get(n) for n in g.liga]
        if None in parts:
            R.e(st, g.name, f"ligature part missing: {g.liga}")
            continue
        a, b = parts
        ok = False
        for shift in range(0, a.w + 1):
            u = set(a.ink()) | {(c + shift, r) for c, r in b.ink()}
            if u == g.ink():
                ok = shift
                break
        if ok is False:
            R.e(st, g.name, f"is not {'+'.join(g.liga)} sharing a stem")
        else:
            R.ok_liga = f"{g.name} = {' + '.join(g.liga)} overlapped by {a.w - ok} column(s): the shared stem"


def check_font(path, R, grid=False):
    st = path.stem.split("-")[1]
    f = TTFont(str(path))
    if f["head"].unitsPerEm != UPM:
        R.e(st, "head", f"UPM {f['head'].unitsPerEm}")
    hh, os2 = f["hhea"], f["OS/2"]
    m = (hh.ascent, hh.descent, hh.lineGap, os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap, os2.usWinAscent, os2.usWinDescent)
    if m != (ASC, DSC, 0, ASC, DSC, 0, ASC, -DSC):
        R.e(st, "metrics", f"vertical metrics {m}")
    if not os2.fsSelection & 0x80:
        R.e(st, "OS/2", "USE_TYPO_METRICS not set")
    gs = f.getGlyphSet()
    glyf = f["glyf"]
    allowed = {0} if not grid else {0, CELL - GRID_GAP["large"]}
    for name in f.getGlyphOrder():
        adv, _ = f["hmtx"][name]
        if adv % CELL:
            R.e(st, name, f"advance {adv} not on the cell grid")
        gl = glyf[name]
        if gl.numberOfContours > 0:
            coords = gl.getCoordinates(glyf)[0]
            for x, y in coords:
                if x % CELL not in allowed or y % CELL not in allowed:
                    R.e(st, name, f"point ({x},{y}) off the cell grid")
                    break
    names = {n.nameID: n.toUnicode() for n in f["name"].names if n.platformID == 3}
    for nid in (0, 1, 2, 4, 5, 6, 13, 14):
        if nid not in names:
            R.e(st, "name", f"nameID {nid} missing")
    if VERSION not in names.get(5, ""):
        R.e(st, "name", f"version {names.get(5)}")
    cmap = f.getBestCmap()
    for cp in range(0xE000, 0xE008):
        if cp not in cmap:
            R.e(st, "cmap", f"U+{cp:04X} unmapped")
    if st != "Bold" and "GSUB" not in f:
        R.e(st, "GSUB", "no liga")
    if st == "Bold" and "GSUB" in f:
        R.e(st, "GSUB", "Bold must not ligate dh (the mark stays one-cell)")
    if "GPOS" in f:
        for lk in f["GPOS"].table.LookupList.Lookup:
            for sub in lk.SubTable:
                for v in values(sub):
                    if v % CELL:
                        R.e(st, "GPOS", f"kern {v} not whole cells")
                        return


def values(sub):
    if sub.Format == 1:
        for ps in sub.PairSet:
            for pvr in ps.PairValueRecord:
                yield getattr(pvr.Value1, "XAdvance", 0) or 0
    else:
        for c1 in sub.Class1Record:
            for c2 in c1.Class2Record:
                yield getattr(c2.Value1, "XAdvance", 0) or 0


def main(a):
    R = Report()
    R.ok_liga = None
    try:
        reg, bold_src = sources()
    except SourceError as e:
        print(f"ERROR source {e}")
        return 1
    bold, fallback = bold_set(reg, bold_src)
    for name in fallback:
        if reg[name].rows and any(reg[name].ink()) and not reg[name].source:
            R.w("Bold", name, "not drawn in bold.s7 yet (auto-bold rule)")
    for st, gl in (("Regular", reg), ("Bold", bold)):
        for g in gl.values():
            check_lines(st, g, R)
            check_stems(st, g, R)
            check_bearings(st, g, R)
        check_tabular(st, gl, R)
        check_charset(st, gl, R)
        check_dups(st, gl, R)
        check_liga(st, gl, R)
    for p in sorted(OUT.glob("Stem7-*.ttf")):
        check_font(p, R, grid="Grid" in p.name)
    for line in R.err + R.warn:
        print(line)
    n = sum(1 for g in reg.values() if g.cps)
    print(f"\n{n} mapped glyphs per style · {len(R.err)} errors · {len(R.warn)} warnings"
          + (f"\nliga: {R.ok_liga}" if R.ok_liga else ""))
    return 1 if R.err or (getattr(a, "strict", False) and R.warn) else 0
