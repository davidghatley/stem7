"""Draw glyphs straight from the source as large bitmaps (no browser): review sheets and before/after crops.

    stemctl review [--style Regular|Bold] [--glyphs A B ...] [--cell 10]   -> proofs/review-*.png
    stemctl diff OLD.s7 [--glyphs ...] -o out.png                          -> old | new, changed glyphs only
"""
from PIL import Image, ImageDraw, ImageFont
from .render import colours

GUIDE_ROWS = (3, 7)  # x-height line (top of row 4) and baseline (top of row 8), in rows from the cap line


def _font(size):
    for p in ("/usr/share/fonts/TTF/IBMPlexMono-Regular.ttf", "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
              "/usr/share/fonts/noto/NotoSansMono-Regular.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def tile(g, cell, C, label=True, mark=None):
    """One glyph on its cell grid. mark = set of (c, r) cells to outline in vermilion (changed cells)."""
    adv = max(g.advance, 1)
    W, H = adv * cell + 1, 9 * cell + 1
    lab_h = 28 if label else 0
    im = Image.new("RGB", (W, H + lab_h), C["sheet"])
    d = ImageDraw.Draw(im)
    if g.lsb:
        d.rectangle([0, 0, g.lsb * cell, H - 1], fill=C["cobalt-tint"])
    rs = adv - g.lsb - g.w
    if rs > 0 and g.rows:
        d.rectangle([(adv - rs) * cell, 0, W - 1, H - 1], fill=C["cobalt-tint"])
    for i in range(adv + 1):
        d.line([i * cell, 0, i * cell, H - 1], fill=C["rule-faint"] if 0 < i < adv else C["rule"])
    for j in range(10):
        d.line([0, j * cell, W - 1, j * cell], fill=C["cobalt"] if j in GUIDE_ROWS else (C["rule"] if j in (0, 9) else C["rule-faint"]))
    for (c, r) in g.ink():
        x, y = (c + g.lsb) * cell, r * cell
        d.rectangle([x + 1, y + 1, x + cell - 1, y + cell - 1], fill=C["ink"])
    for (c, r) in (mark or ()):
        x, y = (c + g.lsb) * cell, r * cell
        d.rectangle([x, y, x + cell, y + cell], outline=C["vermilion"], width=2)
    if label:
        f = _font(11)
        d.text((0, H + 4), g.name[:14], fill=C["ink-muted"], font=f)
    return im


def sheet(glyphs, cell=10, width=1500, theme="light", title=""):
    C = colours()[theme]
    tiles = [tile(g, cell, C) for g in glyphs if g.rows or g.width]
    gap, pad = 14, 24
    rows, cur, x = [], [], pad
    for t in tiles:
        if cur and x + t.width > width - pad:
            rows.append(cur); cur, x = [], pad
        cur.append(t); x += t.width + gap
    if cur:
        rows.append(cur)
    head = 40 if title else 0
    H = pad + head + sum(max(t.height for t in r) + gap for r in rows) + pad
    im = Image.new("RGB", (width, H), C["paper"])
    d = ImageDraw.Draw(im)
    if title:
        d.text((pad, pad), title, fill=C["ink-muted"], font=_font(13))
        d.line([pad, pad + 24, width - pad, pad + 24], fill=C["ink"])
    y = pad + head
    for r in rows:
        x = pad
        for t in r:
            im.paste(t, (x, y)); x += t.width + gap
        y += max(t.height for t in r) + gap
    return im


def diff_image(old, new, names, cell=10, theme="light", title=""):
    """Pairs old | new for each name, changed cells outlined in vermilion on the new side."""
    C = colours()[theme]
    pairs = []
    for n in names:
        a, b = old.get(n), new.get(n)
        if a is None or b is None:
            continue
        ia = tile(a, cell, C)
        ib = tile(b, cell, C, mark=(b.ink() ^ {(c + a.lsb - b.lsb, r) for (c, r) in a.ink()}) if a.w == b.w and a.lsb == b.lsb else None)
        w = ia.width + 24 + ib.width
        h = max(ia.height, ib.height)
        p = Image.new("RGB", (w, h), C["paper"])
        p.paste(ia, (0, 0)); p.paste(ib, (ia.width + 24, 0))
        d = ImageDraw.Draw(p)
        d.text((ia.width + 6, 9 * cell // 2 - 8), ">", fill=C["vermilion"], font=_font(14))
        pairs.append(p)
    if not pairs:
        return None
    pad, gap, width = 24, 28, 1500
    rows, cur, x = [], [], pad
    for t in pairs:
        if cur and x + t.width > width - pad:
            rows.append(cur); cur, x = [], pad
        cur.append(t); x += t.width + gap
    rows.append(cur)
    width = min(width, max(sum(t.width + gap for t in r) for r in rows) + 2 * pad)
    head = 40 if title else 0
    H = pad + head + sum(max(t.height for t in r) + gap for r in rows) + pad - gap
    im = Image.new("RGB", (width, H), C["paper"])
    d = ImageDraw.Draw(im)
    if title:
        d.text((pad, pad), title, fill=C["ink-muted"], font=_font(13))
        d.line([pad, pad + 24, width - pad, pad + 24], fill=C["ink"])
    y = pad + head
    for r in rows:
        x = pad
        for t in r:
            im.paste(t, (x, y)); x += t.width + gap
        y += max(t.height for t in r) + gap
    return im


def text_image(glyphs, text, cell=4, theme="light", kern=None, pad=8):
    """Set a string from source bitmaps (whole cells, optional {(left, right): cells} kerning)."""
    C = colours()[theme]
    cmap = {chr(cp): g for g in glyphs.values() for cp in g.cps}
    lig = {tuple(g.liga): g for g in glyphs.values() if g.liga}
    seq, i = [], 0
    while i < len(text):
        if tuple(text[i:i + 2]) in lig:
            seq.append(lig[tuple(text[i:i + 2])]); i += 2
        else:
            seq.append(cmap.get(text[i], cmap.get("?"))); i += 1
    x, placed = 0, []
    for j, g in enumerate(seq):
        if j and kern:
            x += kern.get((seq[j - 1].name, g.name), 0)
        placed.append((x, g)); x += g.advance
    im = Image.new("RGB", (x * cell + 2 * pad, 9 * cell + 2 * pad), C["paper"])
    d = ImageDraw.Draw(im)
    for x0, g in placed:
        for (c, r) in g.ink():
            X, Y = pad + (x0 + g.lsb + c) * cell, pad + r * cell
            d.rectangle([X, Y, X + cell - 1, Y + cell - 1], fill=C["ink"])
    return im


def stack(images, theme="light", gap=4):
    C = colours()[theme]
    W = max(i.width for i in images)
    im = Image.new("RGB", (W, sum(i.height + gap for i in images)), C["paper"])
    y = 0
    for i in images:
        im.paste(i, (0, y)); y += i.height + gap
    return im
