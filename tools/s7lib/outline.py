"""Cells -> outlines. Regular and Bold merge each glyph's cells into clean, non-overlapping contours;
Grid draws every cell as its own square with a gap on the top and right, so the bottom-left corner of
every square stays on the cell grid (baseline and stems keep their lines)."""

ABOVE = 7  # rows above the baseline


def cell_box(c, r, lsb):
    """(x0, y0, x1, y1) of cell (c, r) in cell units, y up, baseline 0."""
    x0 = c + lsb
    y0 = ABOVE - r - 1
    return x0, y0, x0 + 1, y0 + 1


def trace(filled, lsb=0):
    """Union of unit squares -> contours (lists of integer points, cell units). Outer contours run
    clockwise in y-up space (TrueType direction). At pinch points (two cells touching only at a corner)
    the walk turns right, which keeps diagonal pixels as separate, non-overlapping contours."""
    edges = set()
    for (c, r) in filled:
        x0, y0, x1, y1 = cell_box(c, r, lsb)
        sq = [(x0, y1), (x1, y1), (x1, y0), (x0, y0)]  # clockwise, y up
        for i in range(4):
            a, b = sq[i], sq[(i + 1) % 4]
            if (b, a) in edges:
                edges.discard((b, a))
            else:
                edges.add((a, b))
    nxt = {}
    for a, b in edges:
        nxt.setdefault(a, []).append(b)
    contours = []
    while nxt:
        start = min(nxt)  # deterministic
        pts, cur, prev = [start], start, None
        while True:
            options = nxt[cur]
            if len(options) == 1 or prev is None:
                step = sorted(options)[0]
            else:
                dx, dy = cur[0] - prev[0], cur[1] - prev[1]
                right = (dy, -dx)
                step = next((o for o in options if (o[0] - cur[0], o[1] - cur[1]) == right), options[0])
            options.remove(step)
            if not options:
                del nxt[cur]
            prev, cur = cur, step
            if cur == start:
                break
            pts.append(cur)
        simp = [p for i, p in enumerate(pts)
                if (p[0] - pts[i - 1][0]) * (pts[(i + 1) % len(pts)][1] - p[1])
                - (p[1] - pts[i - 1][1]) * (pts[(i + 1) % len(pts)][0] - p[0]) != 0]
        contours.append(simp)
    return contours


def squares(filled, lsb, gap):
    """Grid style: one square per cell, `gap` (fraction of a cell, as units/cell) cut from top and right."""
    out = []
    for (c, r) in sorted(filled, key=lambda t: (t[1], t[0])):
        x0, y0, x1, y1 = cell_box(c, r, lsb)
        out.append((x0, y0, x1 - gap, y1 - gap))
    return out
