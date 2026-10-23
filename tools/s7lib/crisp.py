"""crisp: render text at every house step in headless Chromium and count anti-aliased pixels.

Black (#000) on white (#fff), so any pixel that is neither 0 nor 255 is anti-aliasing. For each style and
size we set every mapped glyph (and the kerned pairs and the dh ligature) with `line-height: 1` at whole-
pixel offsets, then report grey / ink pixels in the glyph area. We also probe the line box: an `H` must
start on the first pixel row of its box and end exactly 7 cells down (baseline on a whole pixel).
"""
import json
from PIL import Image
from . import FONT_DIR
from .render import shoot, font_faces, esc, STEPS, CRISP_STEPS, WORK
from .fontbuild import sources, bold_set

WIDTH = 1600
FAMILY = {"Regular": ('"Stem 7"', 400), "Bold": ('"Stem 7"', 700), "Grid": ('"Stem 7 Grid"', 400)}


def corpus(glyphs):
    chars = [chr(cp) for g in glyphs.values() if g.rows and any(g.ink()) for cp in g.cps[:1]]
    extra = ["dh", "To", "LT", "r.", "Fa", "“A”", "1,080", "PLATE 2.1 · TILE RULES", "SEED 4127"]
    return chars, extra


def lines_for(glyphs, size, items):
    adv = {chr(cp): g.advance for g in glyphs.values() for cp in g.cps}
    cell = size / 8
    lines, cur, w = [], [], 0
    for it in items:
        iw = sum(adv.get(ch, 6) for ch in it) * cell + 3 * cell
        if cur and w + iw > WIDTH - 4 * size:
            lines.append(" ".join(cur)); cur, w = [], 0
        cur.append(it); w += iw
    if cur:
        lines.append(" ".join(cur))
    return lines


def measure(style, sizes, glyphs):
    fam, wt = FAMILY[style]
    chars, extra = corpus(glyphs)
    blocks, y = [], 8
    for s in sizes:
        lines = lines_for(glyphs, s, chars + extra)
        h = len(lines) * s
        blocks.append((s, y, h, lines))
        y += h + s // 2 + 8
    body = []
    for s, top, h, lines in blocks:
        body.append(f'<div class="t" style="left:{8}px;top:{top}px;font-size:{s}px">H</div>')
        body.append(f'<div class="t" style="left:{8 + 2 * s}px;top:{top}px;font-size:{s}px">'
                    + "\n".join(esc(l) for l in lines) + "</div>")
    page = f"""<!doctype html><meta charset="utf-8"><style>{font_faces()}
html,body{{margin:0;background:#fff}}
.t{{position:absolute;white-space:pre;line-height:1;color:#000;font-family:{fam};font-weight:{wt};
font-synthesis:none;font-kerning:normal;font-variant-ligatures:common-ligatures;letter-spacing:0}}</style>
{''.join(body)}"""
    png = shoot(page, WORK / f"crisp-{style}.png", WIDTH, y + 8)
    im = Image.open(png).convert("RGB")
    W, H = im.size
    px = im.load()
    res = []
    for s, top, h, lines in blocks:
        cell = s / 8
        # glyph area: text region, plus one cell of descender overflow under the box
        x0, x1, y0, y1 = 8 + 2 * s, W, top, min(H, top + h + int(2 * cell) + 1)
        ink = grey = 0
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                r, g, b = px[xx, yy]
                if (r, g, b) != (255, 255, 255):
                    ink += 1
                    if (r, g, b) != (0, 0, 0):
                        grey += 1
        # line-box probe
        rows = [yy for yy in range(top, min(H, top + 2 * s)) if any(px[xx, yy] != (255, 255, 255) for xx in range(8, 8 + 2 * s))]
        first, last = (rows[0] - top, rows[-1] - top + 1) if rows else (None, None)
        # Grid squares carry their gap on top (1/2 cell up to 40 px, 1/3 cell from 48 px), so H starts below the box top
        top_expected = (cell / 2 if s <= 40 else cell / 3) if style == "Grid" else 0
        res.append(dict(style=style, size=s, cell=cell, ink=ink, grey=grey, frac=grey / ink if ink else 0,
                        cap_top=first, cap_top_expected=top_expected, baseline=last, baseline_expected=7 * cell))
    return res


def main(a):
    reg, bold_src = sources()
    bold, _ = bold_set(reg, bold_src)
    styles = a.styles or ["Regular", "Bold", "Grid"]
    sizes = a.sizes or STEPS
    out, fail = [], 0
    print(f"{'style':8} {'px':>4} {'cell':>6} {'ink px':>8} {'grey px':>8} {'grey %':>8}  line box: H top, baseline / expected")
    for st in styles:
        for r in measure(st, sizes, bold if st == "Bold" else reg):
            must = r["size"] in CRISP_STEPS
            ok = (r["grey"] == 0 and r["cap_top"] == r["cap_top_expected"] and r["baseline"] == r["baseline_expected"]) if must else True
            fail += not ok
            flag = ("PASS" if ok else "FAIL") if must else "  - "
            print(f"{r['style']:8} {r['size']:>4} {r['cell']:>6.3g} {r['ink']:>8} {r['grey']:>8} {100 * r['frac']:>7.2f}%  "
                  f"{r['cap_top']}, {r['baseline']} / {r['cap_top_expected']:g}, {r['baseline_expected']:g}   {flag}")
            out.append(r)
    print(f"\nwhole-cell steps {CRISP_STEPS}: {'all crisp' if not fail else f'{fail} FAIL'}")
    if getattr(a, "out", None):
        with open(a.out, "w") as f:
            json.dump(out, f, indent=1)
    return 1 if fail else 0
