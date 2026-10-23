"""proof: PNG proof sheets in light and dark, coloured with tokens.json, rendered by headless Chromium.

Sheets (proofs/<sheet>-<theme>.png):
    charset-regular / charset-bold / charset-grid   every glyph at 48 px (6 px cells) over its cell grid
    waterfall     one line per house step, all three styles
    spacing       nnonnn, HHOHH, ooxoo and friends at 32 px
    kerning       each kerned pair with kerning off and on
    vocabulary    the strings the house actually sets
    pua           the mark, the dh ligature and the pantry glyphs
"""
from . import FONT_DIR, ROOT
from .render import shoot, font_faces, colours, esc, STEPS
from .fontbuild import sources, bold_set, CELL
from . import kern as kernmod

PROOFS = ROOT / "proofs"
WIDTH = 1600
PLEX = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600'
        '&family=Newsreader:ital,opsz,wght@1,6..72,400&display=swap">')
VOCAB = ["PLATE 2.1 · TILE RULES", "SEED 4127", "1,080 TRIS", "64×64 ATLAS · 12 MS", "mise en place", "bonfire",
         "nibble", "napkin", "playdough", "design · AI/ML · generative tools", "dh", "BUILD LOG 07", "HP 12/12",
         "“Decoration carries information.”", "Two inks on plaster — every piece is a plate…", "→ next ↗ open ← back",
         "48°  #07  50%  3×4  v1.0"]
SPACING = ["nnonnnonnnn", "HHOHHOHHH", "ooxooxoo", "nnannennnnsnn", "HHAHHEHHRHH", "0123456789", "H0H1H2H3H4H5H6H7H8H9H",
           "minimum wavy hill", "MINIMUM WAVY HILL"]


def page(theme, body, extra_css=""):
    C = colours()[theme]
    css = f"""{font_faces()}
:root{{--paper:{C['paper']};--sheet:{C['sheet']};--ink:{C['ink']};--muted:{C['ink-muted']};--rule:{C['rule']};
--faint:{C['rule-faint']};--cobalt:{C['cobalt-text']};--verm:{C['vermilion']};--vt:{C['vermilion-text']};--ctint:{C['cobalt-tint']}}}
html,body{{margin:0;background:var(--paper);color:var(--ink)}}
body{{padding:32px;font:400 13px/20px "IBM Plex Mono",ui-monospace,monospace}}
.lab{{font:500 11px/16px "IBM Plex Mono",ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
.head{{display:flex;justify-content:space-between;border-bottom:1px solid var(--ink);padding-bottom:12px;margin-bottom:24px}}
.px{{font-family:"Stem 7";line-height:1;font-synthesis:none;letter-spacing:0;font-variant-ligatures:common-ligatures;white-space:pre}}
.b{{font-weight:700}} .g{{font-family:"Stem 7 Grid"}}
.cap{{font:italic 400 16px/24px Newsreader,Georgia,serif;color:var(--muted);margin-top:16px}}
{extra_css}"""
    return f'<!doctype html><meta charset="utf-8">{PLEX}<style>{css}</style><body data-theme="{theme}">{body}</body>'


def head(title, status):
    return f'<div class="head"><span class="lab">{esc(title)}</span><span class="lab">{esc(status)}</span></div>'


def grid_svg(w_cells, cell, lsb, adv):
    """Cell grid for a glyph box: 9 rows from the cap line; guide lines for cap, x-height, baseline."""
    W, H = adv * cell, 9 * cell
    lines = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="none" stroke="var(--rule)"/>']
    for i in range(1, adv):
        lines.append(f'<line x1="{i*cell}" y1="0" x2="{i*cell}" y2="{H}" stroke="var(--faint)"/>')
    for j in range(1, 9):
        col = "var(--cobalt)" if j in (3, 7) else "var(--faint)"
        lines.append(f'<line x1="0" y1="{j*cell}" x2="{W}" y2="{j*cell}" stroke="{col}"/>')
    # side bearings tinted
    rs = adv - lsb - w_cells
    if lsb:
        lines.insert(0, f'<rect x="0" y="0" width="{lsb*cell}" height="{H}" fill="var(--ctint)"/>')
    if rs:
        lines.insert(0, f'<rect x="{(adv-rs)*cell}" y="0" width="{rs*cell}" height="{H}" fill="var(--ctint)"/>')
    return f'<svg width="{W}" height="{H}" style="position:absolute;left:0;top:0" shape-rendering="crispEdges">{"".join(lines)}</svg>'


def charset(glyphs, style, theme):
    size, cell = 48, 6
    cls = {"Regular": "", "Bold": "b", "Grid": "g"}[style]
    tiles = []
    for g in glyphs.values():
        if not g.cps and not g.liga:
            continue
        text = "".join(chr(c) for c in g.cps[:1]) if g.cps else "".join(g.liga)
        adv = max(g.advance, 1)
        tiles.append(f'<div class="tile"><div class="box" style="width:{adv*cell}px;height:{9*cell}px">{grid_svg(g.w, cell, g.lsb, adv)}'
                     f'<div class="px {cls}" style="position:absolute;left:0;top:0;font-size:{size}px">{esc(text)}</div></div>'
                     f'<div class="nm">{esc(g.name)}<br>{("U+%04X" % g.cps[0]) if g.cps else "liga"} · {g.w}+{adv - g.w}</div></div>')
    css = """.tiles{display:flex;flex-wrap:wrap;gap:20px 16px;align-items:flex-end}.tile{display:flex;flex-direction:column;gap:6px}
.box{position:relative}.nm{font:400 11px/14px "IBM Plex Mono",monospace;color:var(--muted)}"""
    body = head(f"STEM 7 {style.upper()} · CHARSET · 48 PX · 6 PX CELLS", f"{len(tiles)} GLYPHS · {theme.upper()}") + \
        f'<div class="tiles">{"".join(tiles)}</div><p class="cap">Blue rules: x-height and baseline. Tinted columns are side bearings; the numbers under each glyph are ink width + bearings, in cells.</p>'
    return page(theme, body, css)


def waterfall(theme):
    rows = []
    for st, cls in (("Regular", ""), ("Bold", "b"), ("Grid", "g")):
        rows.append(f'<div class="lab" style="margin:24px 0 8px">STEM 7 {st.upper()}</div>')
        for s in STEPS:
            crisp = "whole cells" if s in (16, 32, 48, 72, 120) else "off-grid"
            text = "Tile rules 2.1 · SEED 4127" if s < 72 else ("Tile rules 2.1" if s < 120 else "dh 07")
            rows.append(f'<div class="row"><span class="lab">{s} PX · {s/8:g} PX CELL · {crisp}</span>'
                        f'<span class="px {cls}" style="font-size:{s}px">{esc(text)}</span></div>')
    css = ".row{display:grid;grid-template-columns:260px 1fr;align-items:end;gap:16px;padding:6px 0;border-bottom:1px solid var(--faint)}"
    return page(theme, head("STEM 7 · WATERFALL · HOUSE STEPS", theme.upper()) + "".join(rows) +
                '<p class="cap">Only 16, 32, 48, 72 and 120 land on whole pixels; the others are listed to show why they are not pixel sizes.</p>', css)


def spacing(theme):
    rows = []
    for st, cls in (("Regular", ""), ("Bold", "b")):
        rows.append(f'<div class="lab" style="margin:16px 0 8px">STEM 7 {st.upper()} · 32 PX</div>')
        for s in SPACING:
            rows.append(f'<div class="px {cls}" style="font-size:32px;margin:0 0 20px">{esc(s)}</div>')
    return page(theme, head("STEM 7 · SPACING TESTS", theme.upper()) + "".join(rows))


def kerning(theme, reg, bold):
    rows = []
    for st, cls, gl in (("Regular", "", reg), ("Bold", "b", bold)):
        pairs = kernmod.sample_pairs(st, gl)
        rows.append(f'<div class="lab" style="margin:16px 0 8px">STEM 7 {st.upper()} · 32 PX · KERNING OFF / ON</div><div class="kp">')
        for p in pairs:
            rows.append(f'<div class="pair"><span class="px {cls}" style="font-size:32px;font-kerning:none">{esc(p)}</span>'
                        f'<span class="px {cls}" style="font-size:32px;font-kerning:normal">{esc(p)}</span></div>')
        rows.append("</div>")
    css = """.kp{display:flex;flex-wrap:wrap;gap:12px 32px}.pair{display:flex;gap:16px;padding:8px 12px;background:var(--sheet);border:1px solid var(--rule)}"""
    return page(theme, head("STEM 7 · KERNING PAIRS · WHOLE CELLS", theme.upper()) + "".join(rows), css)


def vocabulary(theme):
    rows = []
    for st, cls in (("Regular", ""), ("Bold", "b"), ("Grid", "g")):
        rows.append(f'<div class="lab" style="margin:16px 0 8px">STEM 7 {st.upper()} · 32 PX</div>')
        for v in VOCAB:
            rows.append(f'<div class="px {cls}" style="font-size:32px;margin:0 0 16px">{esc(v)}</div>')
    rows.append('<div class="lab" style="margin:16px 0 8px">48 PX · 72 PX</div>')
    rows.append('<div class="px" style="font-size:48px;margin:0 0 16px">PLATE 2.1 · TILE RULES</div>')
    rows.append('<div class="px b" style="font-size:72px">SEED 4127</div>')
    return page(theme, head("STEM 7 · HOUSE VOCABULARY", theme.upper()) + "".join(rows))


def pua(theme, reg):
    tiles = []
    for g in reg.values():
        if g.source or g.liga:
            text = chr(g.cps[0]) if g.cps else "dh"
            what = g.source.replace("GLYPHS.", "") if g.source else ""
            tiles.append(f'<div class="t"><span class="px" style="font-size:120px">{esc(text)}</span>'
                         f'<span class="px g" style="font-size:72px">{esc(text)}</span>'
                         f'<span class="lab">{esc(g.name)} · {("U+%04X" % g.cps[0]) if g.cps else "liga d+h"} · {esc(what)}</span></div>')
    css = ".ts{display:flex;flex-wrap:wrap;gap:32px}.t{display:flex;flex-direction:column;gap:12px;padding:16px;background:var(--sheet);border:1px solid var(--rule)}"
    body = head("STEM 7 · PRIVATE USE · MARK AND PANTRY", theme.upper()) + f'<div class="ts">{"".join(tiles)}</div>' + \
        '<div class="lab" style="margin:24px 0 8px">TYPED: d h (no ligature) · dh (ligature)</div>' + \
        '<span class="px" style="font-size:72px;font-variant-ligatures:none">dh</span> <span class="px" style="font-size:72px">dh</span>' + \
        '<p class="cap">The mark and the project glyphs are read from src/house.json at build time.</p>'
    return page(theme, body, css)


def main(a):
    reg, bold_src = sources()
    bold, _ = bold_set(reg, bold_src)
    sheets = {
        "charset-regular": lambda th: (charset(reg, "Regular", th), 1600),
        "charset-bold": lambda th: (charset(bold, "Bold", th), 1600),
        "charset-grid": lambda th: (charset(reg, "Grid", th), 1600),
        "waterfall": lambda th: (waterfall(th), 1600),
        "spacing": lambda th: (spacing(th), 1100),
        "kerning": lambda th: (kerning(th, reg, bold), 1300),
        "vocabulary": lambda th: (vocabulary(th), 1400),
        "pua": lambda th: (pua(th, reg), 1400),
    }
    only = a.only or list(sheets)
    for name in only:
        for th in ("light", "dark"):
            html, w = sheets[name](th)
            h = measure_height(html, w)
            p = shoot(html, PROOFS / f"{name}-{th}.png", w, h)
            print(p.relative_to(FONT_DIR.parent.parent), f"{w}x{h}")


def measure_height(html, w):
    """Render once at a tall height, find the last non-paper row, return a snug height."""
    from PIL import Image
    from .render import WORK
    tmp = shoot(html, WORK / "_measure.png", w, 6000)
    im = Image.open(tmp).convert("RGB")
    bg = im.getpixel((2, 2))
    W, H = im.size
    px = im.load()
    last = 0
    for y in range(H - 1, 0, -4):
        if any(px[x, y] != bg for x in range(0, W, 3)):
            last = y
            break
    return min(6000, last + 36)


def compare(before_dir, strings, out, theme="light", weight=400, title="BEFORE / AFTER"):
    """Each 'size:text' string set with the fonts in before_dir (top) and fonts/ (bottom), side by side."""
    import pathlib
    from .render import font_faces
    before = font_faces(fonts_dir=pathlib.Path(before_dir)).replace('"Stem 7', '"Old Stem 7')
    rows = []
    for spec in strings:
        size, text = spec.split(":", 1)
        rows.append(f'<div class="cmp"><span class="lab">{size} PX</span>'
                    f'<span class="px" style="font-family:\'Old Stem 7\';font-size:{size}px;font-weight:{weight}">{esc(text)}</span>'
                    f'<span class="px" style="font-size:{size}px;font-weight:{weight}">{esc(text)}</span></div>')
    css = before + ".cmp{display:grid;grid-template-columns:90px auto auto;gap:48px;align-items:end;padding:12px 0;border-bottom:1px solid var(--faint)}"
    html = page(theme, head(title, "LEFT: BEFORE · RIGHT: AFTER") + "".join(rows), css)
    w = 1400
    shoot(html, out, w, measure_height(html, w))
    return out
