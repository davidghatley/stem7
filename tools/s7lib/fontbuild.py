"""Build Stem 7 Regular, Bold and Grid (TTF + WOFF2) from the .s7 sources.

The em is 8 cells: UPM 2400, one cell = 300 units = font-size / 8. At the house steps 16, 32, 48, 72 and
120 px a cell is 2, 4, 6, 9 and 15 device pixels, and every outline point, advance, kern and the baseline
land on whole pixels. (2400 rather than 800 so the Grid's gap can be exactly 1/2 or 1/3 of a cell.)

Vertical metrics (all three tables agree, USE_TYPO_METRICS set):
    ascender 2400 (8 cells: 7 cap cells + 1 cell of headroom), descender -600 (2 cells), line gap 0.
With `line-height: 1` the half-leading is -1 cell, so the baseline sits exactly 7 cells below the top of the
line box: the box runs from the cap line to 1 cell under the baseline, at every size.

Grid is a variable font with one axis, opsz (8-160, default 48). The gap is 1/3 cell from opsz 48 up and
1/2 cell at opsz 40 and below. Browsers set opsz to the font size in CSS px (font-optical-sizing: auto),
so the gap is 1 px at 16, 2 px at 32 and 48, 3 px at 72 and 5 px at 120: whole pixels at every step.
"""
import datetime, pathlib
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools import varLib
from fontTools.misc.timeTools import timestampFromString
from fontTools.otlLib.builder import buildStatTable

from . import SRC, OUT, house
from .source import parse, CAP, XH, DESC
from .outline import trace, cell_box

UPM, CELL = 2400, 300
ASC, DSC = 8 * CELL, -DESC * CELL
VERSION = "1.001"
YEAR = 2026
FAMILY = "Stem 7"
COPYRIGHT = f"Copyright {YEAR} David Hatley"
LICENSE = ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
           "This license is available with a FAQ at: https://openfontlicense.org")
GRID_GAP = {"small": CELL // 2, "large": CELL // 3}  # 150 and 100 units


def sources():
    h = house.load()
    reg = parse(SRC / "regular.s7", h)
    bold_path = SRC / "bold.s7"
    bold = parse(bold_path, h) if bold_path.exists() else {}
    return reg, bold


def bold_set(reg, bold):
    """Bold glyphs in Regular's order; anything missing from bold.s7 falls back to the auto-bold rule.
    Ligatures are skipped: Bold has no dh ligature (the mark stays a one-cell drawing)."""
    from .boldrule import embolden
    out, fallback = {}, []
    for name, g in reg.items():
        if g.liga:
            continue
        if name in bold:
            out[name] = bold[name]
        else:
            out[name] = embolden(g)
            fallback.append(name)
    return out, fallback


def read_kern(style):
    """kern-<style>.txt -> feature text in font units (values are whole cells in the file)."""
    p = SRC / f"kern-{style.lower()}.txt"
    if not p.exists():
        return "", 0
    classes, lines, n = {}, [], 0
    for raw in p.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if parts[0] == "class":
            classes[parts[1]] = parts[3:]
            lines.append(f"@{parts[1]} = [{' '.join(parts[3:])}];")
        elif parts[0] == "kern":
            a, b, v = parts[1], parts[2], int(parts[3])
            # a single glyph against a class is enumerated into glyph pairs. Left as a class pair, feaLib puts the
            # glyph in a class subtable where it already has a 0 value (F against R5/R6 lost its -1 that way).
            enum = (a in classes) != (b in classes)
            a = f"@{a}" if a in classes else a
            b = f"@{b}" if b in classes else b
            lines.append(f"{'enum ' if enum else ''}pos {a} {b} {v * CELL};")
            n += 1
    if not n:
        return "", 0
    # single-glyph overrides must come before class pairs, as feaLib requires.
    defs = [l for l in lines if l.startswith("@")]
    glyph_pairs = [l for l in lines if l.startswith("enum") or (l.startswith("pos") and "@" not in l)]
    class_pairs = [l for l in lines if l.startswith("pos") and "@" in l]
    body = "\n".join(glyph_pairs + ["subtable;"] * bool(glyph_pairs and class_pairs) + class_pairs)
    return "\n".join(defs) + f"\nfeature kern {{\n{body}\n}} kern;\n", n


def features(glyphs, style):
    ligas = [g for g in glyphs.values() if g.liga]
    fea = "languagesystem DFLT dflt;\nlanguagesystem latn dflt;\n"
    if ligas:
        fea += "feature liga {\n" + "".join(f"  sub {' '.join(g.liga)} by {g.name};\n" for g in ligas) + "} liga;\n"
    kern, n = read_kern("Regular" if style == "Grid" else style)
    return fea + kern, n


def draw_glyph(g, style, gap=0):
    pen = TTGlyphPen(None)
    if g.rows:
        filled = g.ink()
        if style == "Grid":
            for (c, r) in sorted(filled, key=lambda t: (t[1], t[0])):
                x0, y0, x1, y1 = (v * CELL for v in cell_box(c, r, g.lsb))
                x1, y1 = x1 - gap, y1 - gap
                pen.moveTo((x0, y0)); pen.lineTo((x0, y1)); pen.lineTo((x1, y1)); pen.lineTo((x1, y0)); pen.closePath()
        else:
            for cont in trace(filled, g.lsb):
                pen.moveTo((cont[0][0] * CELL, cont[0][1] * CELL))
                for p in cont[1:]:
                    pen.lineTo((p[0] * CELL, p[1] * CELL))
                pen.closePath()
    return pen.glyph()


def notdef():
    pen = TTGlyphPen(None)
    x0, y0, x1, y1 = 0, 0, 5 * CELL, CAP * CELL
    pen.moveTo((x0, y0)); pen.lineTo((x0, y1)); pen.lineTo((x1, y1)); pen.lineTo((x1, y0)); pen.closePath()
    pen.moveTo((x0 + CELL, y0 + CELL)); pen.lineTo((x1 - CELL, y0 + CELL)); pen.lineTo((x1 - CELL, y1 - CELL)); pen.lineTo((x0 + CELL, y1 - CELL)); pen.closePath()
    return pen.glyph()


def make(glyphs, style, gap=0, family=FAMILY, subfamily="Regular"):
    order = [".notdef"] + list(glyphs)
    cmap = {}
    for g in glyphs.values():
        for cp in g.cps:
            cmap[cp] = g.name
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    glyf = {".notdef": notdef()}
    adv = {".notdef": 6 * CELL}
    for g in glyphs.values():
        glyf[g.name] = draw_glyph(g, style, gap)
        adv[g.name] = g.advance * CELL
    fb.setupGlyf(glyf)
    metrics = {}
    for name in order:
        gl = fb.font["glyf"][name]
        gl.recalcBounds(fb.font["glyf"])
        metrics[name] = (adv[name], getattr(gl, "xMin", 0) if gl.numberOfContours else 0)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASC, descent=DSC, lineGap=0)
    ps_family = family.replace(" ", "")
    ps = f"{ps_family}-{subfamily}"
    bold = subfamily == "Bold"
    fb.setupNameTable({
        "copyright": COPYRIGHT,
        "familyName": family,
        "styleName": subfamily,
        "uniqueFontIdentifier": f"{VERSION};DHAT;{ps}",
        "fullName": f"{family} {subfamily}" if subfamily != "Regular" else family,
        "version": f"Version {VERSION}",
        "psName": ps,
        "manufacturer": "David Hatley",
        "designer": "David Hatley",
        "description": "A pixel face drawn on the grid of the dh mark: 7-cell caps, 4-cell x-height, "
                       "2-cell descender, one cell = font-size / 8.",
        "licenseDescription": LICENSE,
        "licenseInfoURL": "https://openfontlicense.org",
    })
    fs = (0x20 if bold else 0x40) | 0x80  # BOLD or REGULAR, plus USE_TYPO_METRICS
    fb.setupOS2(version=4, usWeightClass=700 if bold else 400, usWidthClass=5, fsType=0, achVendID="DHAT",
                fsSelection=fs, sTypoAscender=ASC, sTypoDescender=DSC, sTypoLineGap=0,
                usWinAscent=ASC, usWinDescent=-DSC, sxHeight=XH * CELL, sCapHeight=CAP * CELL,
                ySubscriptXSize=CELL * 5, ySubscriptYSize=CELL * 5, ySubscriptYOffset=CELL,
                ySuperscriptXSize=CELL * 5, ySuperscriptYSize=CELL * 5, ySuperscriptYOffset=CELL * 4,
                yStrikeoutSize=CELL, yStrikeoutPosition=4 * CELL,
                usDefaultChar=0, usBreakChar=0x20, usMaxContext=2)
    fb.setupPost(isFixedPitch=0, underlinePosition=-CELL, underlineThickness=CELL)
    stamp = timestampFromString("Thu Oct 22 00:00:00 2026")  # fixed, so builds are reproducible
    fb.setupHead(fontRevision=float(VERSION), unitsPerEm=UPM, macStyle=1 if bold else 0, created=stamp, modified=stamp)
    fb.font["head"].flags |= 0x0008  # integer ppem scaling (x/y): our coordinates are all on the cell grid
    fea, nkern = features(glyphs, style)
    addOpenTypeFeaturesFromString(fb.font, fea)
    fb.font["OS/2"].recalcUnicodeRanges(fb.font)
    return fb.font, nkern


def make_grid(reg):
    """Variable Grid: masters at opsz 8 (gap 1/2) and opsz 48 (gap 1/3); avar holds 8..40 at the small gap."""
    small, _ = make(reg, "Grid", GRID_GAP["small"], f"{FAMILY} Grid")
    large, nkern = make(reg, "Grid", GRID_GAP["large"], f"{FAMILY} Grid")
    ds = DesignSpaceDocument()
    ax = AxisDescriptor()
    ax.tag, ax.name, ax.minimum, ax.default, ax.maximum = "opsz", "Optical size", 8, 48, 160
    ax.map = [(8, 8), (40, 8), (48, 48), (160, 160)]
    ax.labelNames = {"en": "Optical size"}
    ds.addAxis(ax)
    for loc, font in ((8, small), (48, large)):
        s = SourceDescriptor()
        s.font, s.location, s.name = font, {"Optical size": loc}, f"opsz{loc}"
        ds.addSource(s)
    vf, _, _ = varLib.build(ds)
    buildStatTable(vf, [dict(tag="opsz", name="Optical size", values=[
        dict(value=16, name="Small", rangeMinValue=8, rangeMaxValue=44),
        dict(value=48, name="Regular", rangeMinValue=44, rangeMaxValue=160, flags=0x2)])])
    return vf, nkern


def save(font, stem):
    OUT.mkdir(exist_ok=True)
    ttf = OUT / f"{stem}.ttf"
    font.save(str(ttf))
    font.flavor = "woff2"
    font.save(str(OUT / f"{stem}.woff2"))
    font.flavor = None
    return ttf, OUT / f"{stem}.woff2"


def build(styles=("Regular", "Bold", "Grid")):
    reg, bold_src = sources()
    report = []
    for st in styles:
        if st == "Regular":
            font, nk = make(reg, "Regular")
            note = ""
        elif st == "Bold":
            glyphs, fallback = bold_set(reg, bold_src)
            font, nk = make(glyphs, "Bold", subfamily="Bold")
            note = f" ({len(fallback)} glyphs from the auto-bold rule: {' '.join(fallback[:12])}{' ...' if len(fallback) > 12 else ''})" if fallback else ""
        else:
            font, nk = make_grid(reg)
            note = " (variable, opsz 8-160)"
        ttf, woff = save(font, f"Stem7-{st}")
        report.append(f"{ttf.name:22} {ttf.stat().st_size:6} B   {woff.name:24} {woff.stat().st_size:6} B   "
                      f"{len(font.getGlyphOrder())} glyphs, {nk} kern pairs{note}")
    return report
